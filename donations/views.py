

import stripe
from django.conf import settings

# Create your views here.
from rest_framework import status, views, permissions

from donations.serializers import DonationSerializer


stripe.api_key = settings.STRIPE_TEST_SECRET_KEY


# from .serializers import DonationsSerializer

#
# class DonationApiView(views.APIView):
#     # change this to is owner Permission
#     permission_classes = [AllowAny]
#     serializer_class = DonationsSerializer
#
#     def post(self, request, *args, **kwargs):
#         data = request.data
#         name = data['insta_username']
#         email = data['email']
#         amount = int(data['amount'])
#         payment_method_id = data['payment_method_id']
#
#         # creating customer
#         customer = stripe.Customer.create(
#             name=name,
#             email=email, payment_method=payment_method_id)
#
#         charge = stripe.Charge.create(
#             customer=customer,
#             amount=amount * 100,
#             currency='usd',
#             description="Donation"
#         )
#
#         return Response(status=status.HTTP_200_OK,
#                         data={
#                             'message': 'Success',
#                             'data': {'customer_id': customer.id}
#                         }
#                         )


def save_stripe_info(request):
    data = request.data
    email = data['email']
    payment_method_id = data['payment_method_id']

    # creating customer
    customer = stripe.Customer.create(email=email, payment_method=payment_method_id)

    charge = stripe.Charge.create(
        customer=customer,
        amount=5 * 100,
        currency='usd',
        description="Donation"
    )

    return views.Response({'status': True, "message": "Success", 'data': {'customer_id': customer.id}},
                          status=status.HTTP_200_OK)


class DonationRequestView(views.APIView):
    schema = None
    permission_classes = (permissions.AllowAny,)
    serializer_class = DonationSerializer

    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(data=data)
        if serializer.is_valid(raise_exception=True):
            amount = int(data['amount'])
            intent = stripe.PaymentIntent.create(
                amount=amount * 100,
                currency='usd',
                payment_method_types=['card'],
            )
            print("Client_ Secret")
            return views.Response(
                {'status': True, "message": "Success", 'data': {'client_secret': intent.client_secret}},
                status=status.HTTP_200_OK)
        else:
            return views.Response(
                {'status': False, "message": "failed", 'data': {}},
                status=status.HTTP_200_OK)