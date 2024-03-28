# Create your views here.
import os

import redis
import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import views, status
from rest_framework.permissions import IsAuthenticated

from accounts.models import User
from beats.models import Songs, PlayList
from beats.permissions import IsSongUserOrReadOnly, IsPlaylistUserOrReadOnly
from feeds.utils import create_action
from .serializers import RedeemCoinsSerializer
from redeemCoins.tasks import send_email_after_buying_coins

# connect to redis
redis_cache = redis.StrictRedis(host=settings.REDIS_HOST,
                                port=settings.REDIS_PORT,
                                db=settings.REDIS_DB)


# class RedeemCoinsFeaturedAPIView(ListAPIView):
#     pagination_class = StandardResultsSetPagination
#     permission_classes = [IsAuthenticated]
#     serializer_class = FeaturedSerializer
#     queryset = Featured.objects.all()
#
#     def get(self, request, *args, **kwargs):
#         # Display all actions by default
#         featured_things = self.queryset.select_related('user__profile').prefetch_related('target')[:10]
#
#         page = self.pagination_class()
#         resp_obj = page.generate_response(featured_things, FeaturedSerializer, request)
#         return resp_obj


class RedeemCoinsForFeaturedSong(views.APIView):
    permission_classes = [IsSongUserOrReadOnly]
    serializer_class = RedeemCoinsSerializer
    queryset = Songs.objects.all()
    schema = None

    def post(self, request, *args, track_id, **kwargs):

        try:
            coins = int(request.POST.get('coins'))
            song_object = get_object_or_404(self.queryset, id=track_id, user=request.user.id)

            current_coins = redis_cache.hget('users:{}:coins'.format(request.user.id), request.user.id)
            # if user coins is 100, he can feature his track on featured tab view
            if int(current_coins) >= coins:
                create_action(request.user, 'featured songs', song_object, 4)
                redis_cache.hincrby('users:{}:coins'.format(request.user.id), request.user.id, -coins)
                return views.Response({'status': True, "message": "song is added on featured"},
                                      status=status.HTTP_200_OK)
            else:
                return views.Response(
                    {'status': False, "message": "your coins are insufficient for this.", 'result': {}},
                    status=status.HTTP_200_OK)
        except TypeError:
            return views.Response({'status': False, "message": "something wrong or may be you don't have any coin",
                                   'result': {}}, status=status.HTTP_200_OK)


class RedeemCoinsForFeaturedPlaylist(views.APIView):
    permission_classes = [IsPlaylistUserOrReadOnly]
    serializer_class = RedeemCoinsSerializer
    queryset = PlayList.objects.all()
    schema = None

    def post(self, request, *args, slug, **kwargs):

        try:
            coins = int(request.POST.get('coins'))
            playlist_object = get_object_or_404(self.queryset, slug=slug, owner=request.user.id)
            current_coins = redis_cache.hget('users:{}:coins'.format(request.user.id), request.user.id)
            # if user coins is 100, he can featured his track on featured tab view
            if int(current_coins) >= coins:
                create_action(request.user, 'featured playlist', playlist_object, 5)
                current_coins = redis_cache.hincrby('users:{}:coins'.format(request.user.id), request.user.id, -coins)

                user = get_object_or_404(User, email=request.user.email)

                data = {'username': user.username, 'email': user.email, 'current_coins': int(current_coins)}

                send_email_after_buying_coins.delay(data)

                return views.Response({'status': True, "message": "playlist is added on featured"},
                                      status=status.HTTP_200_OK)
            else:
                return views.Response(
                    {'status': False, "message": "your coins are insufficient for this.", 'result': {}},
                    status=status.HTTP_200_OK)
        except TypeError:
            return views.Response({'status': False, "message": "something wrong or may be you don't have any coin.",
                                   'result': {}}, status=status.HTTP_200_OK)


class CreatePurchaseCoinsApiView(views.APIView):
    schema = None
    if settings.DEBUG:
        stripe.api_key = settings.STRIPE_TEST_SECRET_KEY
    else:
        stripe.api_key = settings.STRIPE_LIVE_SECRET_KEY
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        price = request.data['price']
        customer_email = request.data['email']
        # customer_id = request.data['customer_id']
        try:
            # Create new Checkout Session for the order
            # Other optional params include:
            # [billing_address_collection] - to display billing address details on the page
            # [customer] - if you have an existing Stripe Customer ID
            # [customer_email] - lets you prefill the email input in the form
            # For full details see https:#stripe.com/docs/api/checkout/sessions/create

            # ?session_id={CHECKOUT_SESSION_ID} means the redirect will have the session ID set as a query param

            checkout_session = stripe.checkout.Session.create(
                success_url='http://localhost:3000/successbuyc/{CHECKOUT_SESSION_ID}',
                cancel_url='http://localhost:3000/cancelbuyc',
                # customer=customer_id,
                customer_email=customer_email,
                allow_promotion_codes=True,
                payment_method_types=['card'],
                metadata={"product_id": price},
                mode='payment',
                line_items=[{
                    'price': price,
                    'quantity': 1,

                }],
            )

            return views.Response(checkout_session, status=status.HTTP_200_OK)
        except Exception as e:
            return views.Response({'error': {'message': str(e)}})


class GetPurchaseCoinsCheckoutSession(views.APIView):
    permission_classes = [IsAuthenticated]
    schema = None

    def get(self, request, session_id, *args, **kwargs):
        try:
            id = session_id
            checkout_session = stripe.checkout.Session.retrieve(id)

            # line_items = stripe.checkout.Session.list_line_items(id, limit=1)
            # # print(line_items['data'][0]['price']['id'])
            #
            # if line_items['data'][0]['price']['id'] == os.getenv('COIN_PRODUCT_100'):
            #coin_amount = redis_cache.hincrby('users:{}:coins'.format(request.user.id), request.user.id, 200)
            resp_obj = dict(
             #   coin_amount=coin_amount,
                checkout_session=checkout_session
            )
            user = User.objects.filter(email=request.user.email)
            data = {'username': user.username, 'email': user.email}

            return views.Response(resp_obj, status=status.HTTP_200_OK)
            # else:
            #     return views.Response({'error': {'message': 'no product found'}}, status=status.HTTP_200_OK)

        except Exception as e:
            return views.Response({'error': {'message': str(e)}}, status=status.HTTP_200_OK)
