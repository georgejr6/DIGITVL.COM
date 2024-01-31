import os

import djstripe
import redis
import stripe
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import views, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import User
from accounts.serializers import GetFullUserSerializer
from subscriptions.models import UserSubscription, UserMembership, Membership
from subscriptions.serializers import UserSubscriptionSerializer
from subscriptions.tasks import send_email_after_subscription
from redeemCoins.tasks import send_email_after_buying_coins

stripe.api_version = '2020-08-27'
# connect to redis
redis_cache = redis.StrictRedis(host=settings.REDIS_HOST,
                                port=settings.REDIS_PORT,
                                db=settings.REDIS_DB)


# getting details of the user subscription plan
class UserSubscriptionDetail(views.APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSubscriptionSerializer

    def get(self, request, *args, **kwargs):
        user_subscription = UserSubscription.objects.filter(user_membership__user__username=request.user.username)

        resp_obj = dict(
            subcription_data=self.serializer_class(user_subscription, context={"request": request}, many=True).data,

        )
        return views.Response(resp_obj, status=status.HTTP_200_OK)


def get_user_membership(request):
    user_membership_qs = UserMembership.objects.filter(user=request.user)
    if user_membership_qs.exists():
        return user_membership_qs.first()
    return None


def get_user_subscription(request):
    user_subscription_qs = UserSubscription.objects.filter(user_membership=get_user_membership(request))
    if user_subscription_qs.exists():
        user_subscription = user_subscription_qs.first()
        return user_subscription
    return None


# view for creating subscriptions of the user

class CreateSubscriptionApiView(views.APIView):
    if settings.DEBUG:
        stripe.api_key = settings.STRIPE_TEST_SECRET_KEY
    else:
        stripe.api_key = settings.STRIPE_LIVE_SECRET_KEY
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            price = request.data['price']
            customer_id = request.data['customer_id']
            customer_email = request.data['email']

            # Create new Checkout Session for the order
            # Other optional params include:
            # [billing_address_collection] - to display billing address details on the page
            # [customer] - if you have an existing Stripe Customer ID
            # [customer_email] - lets you prefill the email input in the form
            # For full details see https:#stripe.com/docs/api/checkout/sessions/create

            # ?session_id={CHECKOUT_SESSION_ID} means the redirect will have the session ID set as a query param

            checkout_session = stripe.checkout.Session.create(
                success_url='http://localhost:3000/success-sub/{CHECKOUT_SESSION_ID}',
                cancel_url='http://localhost:3000/cancel-sub',
                payment_method_types=['card'],
                customer=customer_id,
                allow_promotion_codes=True,
                mode='subscription',
                metadata={'price_id': price},
                line_items=[{
                    'price': price,
                    'quantity': 1
                }],

            )
            print(checkout_session)
            return views.Response(checkout_session, status=status.HTTP_200_OK)
        except Exception as e:
            return views.Response({'error': {'message': str(e)}})


# Fetch the Checkout Session to display the JSON result on the success page

class GetCheckoutSession(views.APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GetFullUserSerializer

    def get(self, request, session_id, *args, **kwargs):
        try:
            id = session_id
            checkout_session = stripe.checkout.Session.retrieve(id)
            customer = stripe.Customer.retrieve(id=checkout_session.customer)
            price_id = os.getenv('BASIC_PRICE_ID')
            selected_membership = Membership.objects.get(stripe_plan_id=price_id)

            # fetch user data from UserMembership table
            user_membership = UserMembership.objects.get(user=request.user)

            user_membership.membership = selected_membership
            user_membership.volume_remaining = selected_membership.storage_size
            user_membership.subscription_badge = True
            user_membership.save()

            djstripe.models.Customer.sync_from_stripe_data(customer)

            subscription = stripe.Subscription.retrieve(id=checkout_session.subscription)
            djstripe_subscription = djstripe.models.Subscription.sync_from_stripe_data(subscription)

            # for email purpose
            # data = {'username': user_membership.user.username, 'email': user_membership.user.email,
            #         'subscription_plan': subscription.plan.product}
            # send_email_after_subscription.delay(data)

            # subscription.subscription.plan.product -> fetch the plan name

            user_subscription = UserSubscription.objects.get(user_membership=user_membership)

            user_subscription.stripe_subscription_id = checkout_session.subscription
            user_subscription.subscription = djstripe_subscription
            user_subscription.save()

            user_membership_data = User.objects.filter(username=request.user.username)
            resp_obj = dict(
                user_membership_data=self.serializer_class(user_membership_data, context={"request": request},
                                                           many=True).data,
                session_data=checkout_session

            )

            return views.Response(resp_obj, status=status.HTTP_200_OK)
        except Exception as e:
            return views.Response({'error': {'message': str(e)}}, status=status.HTTP_200_OK)


class GetCheckoutSessionData(views.APIView):
    # permission_classes = [IsAuthenticated]
    serializer_class = GetFullUserSerializer
    queryset = User.objects.all()

    def get(self, request, username, *args, **kwargs):
        try:
            user_membership_data = User.objects.filter(username=username)
            resp_obj = dict(
                user_membership_data=self.serializer_class(user_membership_data, context={"request": request},
                                                           many=True).data,

            )

            return views.Response(resp_obj, status=status.HTTP_200_OK)
        except Exception as e:
            return views.Response({'error': {'message': str(e)}}, status=status.HTTP_200_OK)


class CreateCustomerPortalApiView(views.APIView):
    permission_classes = [IsAuthenticated]

    # Authenticate your user.
    def post(self, request, *args, **kwargs):
        try:
            customer_id = request.data['customer_id']

            session = stripe.billing_portal.Session.create(customer=customer_id,
                                                           return_url='http://127.0.0.1:3000')
            print(session)
            return views.Response(session, status=status.HTTP_200_OK)

        except Exception as e:
            return views.Response({'error': {'message': str(e)}}, status=status.HTTP_200_OK)


@require_http_methods(["POST"])
@csrf_exempt
def webhook_received(request):
    print("----------------- webhook --------------------------")
    # You can use webhooks to receive information about asynchronous payment events.
    # For more about our webhook events check out https://stripe.com/docs/webhooks.
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    request_data = request.body

    if webhook_secret:
        # Retrieve the event by verifying the signature using the raw body and secret if webhook signing is configured.
        signature = request.headers.get('stripe-signature')

        try:
            event = stripe.Webhook.construct_event(payload=request.body, sig_header=signature, secret=webhook_secret)
            data = event['data']
        except Exception as e:
            return Response(status=400)
        # Get the type of webhook event sent - used to check the status of PaymentIntents.
        event_type = event['type']
    else:
        data = request_data['data']
        event_type = request_data['type']
    data_object = data['object']

    print('event ' + event_type)

    if event_type == 'customer.subscription.created':
        # fetch detail from User Membership table
        user_membership = get_object_or_404(UserMembership, customer__id=data_object.customer)
        data = {'username': user_membership.user.username, 'email': user_membership.user.email,
                'subscription_plan': data_object.subscription.plan.product}
        send_email_after_subscription.delay(data)

    if event_type == 'customer.subscription.deleted':
        print('🔔 subscription deleted!')
        print(data_object.customer)
        free_membership = get_object_or_404(Membership, membership_type='Free')

        # create stripe customer
        stripe_customer = stripe.Customer.retrieve(
            id=data_object.customer
        )

        djstripe_customer = djstripe.models.Customer.sync_from_stripe_data(stripe_customer)

        user_membership = UserMembership.objects.filter(customer__id=data_object.customer).update(
            membership=free_membership, volume_remaining=free_membership.storage_size,
            customer=djstripe_customer, subscription_badge=False)
        print(user_membership)

        stripe_subscription = stripe.Subscription.modify(
            customer=stripe_customer["id"],
            items=[{'price': os.getenv('BASIC_PRICE_ID')}],

        )

        # sync data with subscription dj stripe
        djstripe_subscription = djstripe.models.Subscription.sync_from_stripe_data(stripe_subscription)

        subscription_data = djstripe_subscription

        update_subscription = UserSubscription.objects.filter(
            user_membership=user_membership
        ).update(stripe_subscription_id=stripe_subscription["id"], subscription=subscription_data)

    if event_type == 'checkout.session.completed':

        if data_object.metadata.product_id == os.getenv('COIN_PRODUCT_100'):
            user = get_object_or_404(User, email=data_object.customer_email)
            coin_amount = redis_cache.hincrby('users:{}:coins'.format(user.id), user.id, 100)
            data = {'username': user.username, 'current_coin': coin_amount, 'email': user.email}
            send_email_after_buying_coins.delay(data)

        if data_object.metadata.product_id == os.getenv('COIN_PRODUCT_250'):
            user = get_object_or_404(User, email=data_object.customer_email)
            coin_amount = redis_cache.hincrby('users:{}:coins'.format(user.id), user.id, 250)
            data = {'username': user.username, 'current_coin': coin_amount, 'email': user.email}
            send_email_after_buying_coins.delay(data)

        if data_object.metadata.product_id == os.getenv('COIN_PRODUCT_500'):
            user = get_object_or_404(User, email=data_object.customer_email)
            coin_amount = redis_cache.hincrby('users:{}:coins'.format(user.id), user.id, 500)
            data = {'username': user.username, 'current_coin': coin_amount, 'email': user.email}
            send_email_after_buying_coins.delay(data)

    if event_type == 'billing_portal.configuration.created':
        print(' handle billing portal info  ')
        print(data)

    if event_type == 'billing_portal.configuration.updated':
        print(' billing portal updated ')
        print(data)

    return HttpResponse({'status': status.HTTP_200_OK})
