import redis
from django.conf import settings
from django.contrib.auth import logout as django_logout
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status, views
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Profile, User, Contact
from .permission import IsOwnerOrReadOnly
from .serializers import (GetFullUserSerializer, UpdateProfileSerializer, UserSerializerWithToken,
                          EmailVerificationSerializer, ResetPasswordRequestSerializer, ResetPasswordSerializer,
                          Important_Notification, CustomTokenObtainPairSerializer)
from accounts.tasks import send_email_verification_token
from .utils import Util

# connect to redis
redis_cache = redis.StrictRedis(host=settings.REDIS_HOST,
                                port=settings.REDIS_PORT,
                                db=settings.REDIS_DB)


class CurrentUserApiView(views.APIView):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()

    @swagger_auto_schema(operation_description="Get Current User By Sending JWT Token In Header.")
    def get(self, request, *args, **kwargs):
        """
        Determine the current user by their token, and return their data
        """

        serializer = GetFullUserSerializer(request.user, context={'request': request})
        return Response(serializer.data)


class UserList(APIView):

    """
    Create a new user. It's called 'UserList' because normally we'd have a get
    method here too, for retrieving a list of all User objects.
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(operation_description="Create a new user.\n\n"
                              "This endpoint allows clients to register a new user by submitting their details. "
                              "Upon successful creation of the user, an email verification link will be sent "
                              "to the provided email address.\n\n"
                              "The response includes a success message and status information.\n\n Required Field: username, phone_number, email, password. \n\n phone_number should be entered in the format of +123-456-7890",
                         request_body=UserSerializerWithToken,
                         responses={200: openapi.Response('Response description', UserSerializerWithToken)})
    def post(self, request, *args, **kwargs):
        current_site = get_current_site(None)
        print('post')
        error_result = {}

        serializer = UserSerializerWithToken(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            user_data = serializer.data
            # refresh = RefreshToken.for_user(user)
            # access_token = str(refresh.access_token)
            token = Token.objects.get(user_id=user_data['id'])
            request = HttpRequest()

            # Get the current site
            current_site = get_current_site(request)

            # Get the protocol used in the request (HTTP or HTTPS)
            protocol = 'https' if request.is_secure() else 'http'

            # Generate the absolute URL with the correct protocol
            absolute_url = f'{protocol}://{current_site.domain}/email-verify/{token}'


            email_body = 'Hey' + user_data['username'] + ' use the link below to verify your email \n' \
                         + absolute_url
            data = {'email_body': email_body, 'to_email': user_data['email'], 'username': user_data['username'],
                    'email_subject': 'Verify your email'}

            send_email_verification_token.delay(data)
            output = "Successfully account created, please check your provided email for verification."
            content = {'status': True, 'message': output}
            return Response(content, status=status.HTTP_200_OK)
        content = {'status': False, 'message': serializer.errors, 'result': error_result}
        return Response(content, status=status.HTTP_200_OK)


class ProfileUpdateAPIView(UpdateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsOwnerOrReadOnly]
    lookup_field = 'user_id'
    serializer_class = UpdateProfileSerializer
    queryset = Profile.objects.all()

    def patch(self, request, *args, **kwargs):

        instance = self.get_object()
        serializer = UpdateProfileSerializer(instance=instance, data=request.data,
                                             partial=True, context={'request': request})  # set partial=True to
        # update a data partially
        if serializer.is_valid():

            serializer.save()
            output = "Successfully account updated"
            content1 = {'success': [output]}
            content = {'status': True, 'message': content1, 'result': serializer.data}
            return Response(content, status=status.HTTP_200_OK)
        else:
            content = {'status': False, 'message': serializer.errors, 'result': {}}
            return Response(content, status=status.HTTP_200_OK)


class LogoutView(APIView):
    # authentication_classes = [JSONWebTokenAuthentication, ]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        django_logout(request)
        return Response(status=204)


# class LoginView(ObtainJSONWebToken):
class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
        except AuthenticationFailed as e:
            # Handle the authentication failed exception
            error_message = 'Invalid email or password.'
            return self.custom_error_response(error_message)

        return self.process_response(response)

    def process_response(self, response):
        res = response.data

        if response.status_code == 200 and 'access' in res:
            email = self.request.data.get('email')
            user = User.objects.filter(email=email).first()

            if user:
                if not user.is_email_verified:
                    error_message = 'Please verify your email address. we sent you email verification on your email account.'
                    token = Token.objects.get(user_id=user.id)
                    request = HttpRequest()

                    # Get the current site
                    current_site = get_current_site(request)

                    # Get the protocol used in the request (HTTP or HTTPS)
                    protocol = 'https' if request.is_secure() else 'http'

                    # Generate the absolute URL with the correct protocol
                    absolute_url = f'{protocol}://{current_site.domain}/email-verify/{token}'

                    email_body = 'Hey,' + user.username + ' use the link below to verify your email \n' \
                                 + absolute_url
                    data = {'email_body': email_body, 'to_email': user.email, 'username': user.username,
                            'email_subject': 'Verify your email'}

                    send_email_verification_token.delay(data)
                    return self.custom_error_response(error_message)
                elif not user.check_password(self.request.data.get('password')):
                    error_message = 'Invalid email or password.'
                    return self.custom_error_response(error_message)

                serializer = GetFullUserSerializer(user,  context={'request': self.request})
                res['user'] = serializer.data
            else:
                error_message = 'Invalid email or password.'
                return self.custom_error_response(error_message)

        return Response(res)

    def custom_error_response(self, error_message):
        return Response({
            'status': False,
            'message': error_message,
            'result': {}
        }, status=status.HTTP_200_OK)



class AlternativeLoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
        except AuthenticationFailed as e:
            # Handle the authentication failed exception
            error_message = 'Invalid email or password.'
            return self.custom_error_response(error_message)

        return self.process_response(response)

    def process_response(self, response):
        res = response.data
        current_coins = 0

        if response.status_code == 200 and 'access' in res:
            email = self.request.data.get('email')
            try:
                user = User.objects.get(email=email)
                try:
                    current_coins = redis_cache.hget('users:{}:coins'.format(user.id), user.id)
                except redis.ConnectionError:
                    pass
                if not user.is_email_verified:
                    error_message = 'Please verify your email address. we sent you email verification on your email account.'
                    token = Token.objects.get(user_id=user.id)
                    request = HttpRequest()

                    # Get the current site
                    current_site = get_current_site(request)

                    # Get the protocol used in the request (HTTP or HTTPS)
                    protocol = 'https' if request.is_secure() else 'http'

                    # Generate the absolute URL with the correct protocol
                    absolute_url = f'{protocol}://{current_site.domain}/email-verify/{token}'

                    email_body = 'Hey,' + user.username + ' use the link below to verify your email \n' \
                                 + absolute_url
                    data = {'email_body': email_body, 'to_email': user.email, 'username': user.username,
                            'email_subject': 'Verify your email'}

                    send_email_verification_token.delay(data)
                    return self.custom_error_response(error_message)
                elif not user.check_password(self.request.data.get('password')):
                    error_message = 'Invalid email or password.'
                    return self.custom_error_response(error_message)

                serializer = GetFullUserSerializer(user, context={'request': self.request})
                user_data = serializer.data

                if current_coins:
                    user_data['coins'] = int(current_coins)
                else:
                    user_data['coins'] = 0

                result_data = {

                    'access': res.get('access'),
                    'refresh': res.get('refresh'),
                    'user': user_data,  # User-specific information from the serializer
                    # Include other fields from res as needed
                }

                return Response({
                    'status': True,
                    'message': 'Successful login.',
                    'result': result_data
                }, status=status.HTTP_200_OK)


            except User.DoesNotExist:
                error_message = 'Invalid email or password.'
                return self.custom_error_response(error_message)



    def custom_error_response(self, error_message):
        return Response({
            'status': False,
            'message': error_message,
            'result': {}
        }, status=status.HTTP_200_OK)

class VerifyEmail(views.APIView):
    serializer_class = EmailVerificationSerializer
    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema(operation_description="API For Verification of the User Email \n\n",
                         request_body=EmailVerificationSerializer,
                         responses={200: openapi.Response('Response description', EmailVerificationSerializer)})
    def post(self, request, *args, **kwargs):
        # try:
        result = request.data
        token = str(request.POST.get('token'))
        # payload = jwt_decode_handler(token)
        user = User.objects.get(email_verification_token=token)
        # serializer = UserSerializerWithToken(user, context={'request': request})
        if not user.is_email_verified:
            user.is_email_verified = True
            to_follow = User.objects.get(id=2)

            obj_id = Contact.objects.get_or_create(
                user_from=user,
                user_to=to_follow)

            data = {'username': user.username, 'user_email': user.email,
                    'is_email_verified': user.is_email_verified}

            # send_welcome_email.delay(data)
            # send_coin_to_referral_user(data)
            user.save()

            return Response({'status': True, 'email': 'Successfully activated'}, status=status.HTTP_200_OK)
        else:
            return Response({'status': True, 'email': 'your account is already verified'},
                            status=status.HTTP_200_OK)
    # except Exception:
    #     return Response({'status': False, 'error': 'please provide correct token'}, status=status.HTTP_200_OK)


class ResetPasswordRequestView(views.APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = ResetPasswordRequestSerializer

    @swagger_auto_schema(operation_description="API For Forgot Password Request. \n\n",
                         request_body=ResetPasswordRequestSerializer,
                         responses={
                             200: openapi.Response(
                                 description="Email Sent to your provided email, Please follow the steps to add new password.",
                                 schema=ResetPasswordRequestSerializer
                             )
                         }
                         )
    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(data=data)
        if serializer.is_valid(raise_exception=True):
            response = dict()
            email = serializer.data['email']
            try:
                user = User.objects.get(email=email)
                if user:
                    response['email'] = user.email

                    response['full_name'] = user.get_full_name()
                    response['status'] = True
                    response['message'] = "Email Sent to your provided email, Please follow the steps to add new password."

                    user.reset_password()
                    status_code = status.HTTP_200_OK
                    return views.Response(response, status=status_code)
            except User.DoesNotExist:
                response['status'] = False
                status_code = status.HTTP_200_OK
                response['message'] = "Could not find user"
                return views.Response(response, status=status_code)


class ResetPasswordView(views.APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = ResetPasswordSerializer

    swagger_auto_schema(operation_description="API For Resetting the User Password. \n\n",
                       request_body=ResetPasswordRequestSerializer,
                       responses={
                           200: openapi.Response(
                               description="Email Sent to your provided email, Please follow the steps to add new password.",
                               schema=ResetPasswordRequestSerializer
                           )
                       }
                       )

    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(data=data)
        if serializer.is_valid(raise_exception=True):
            response = dict()
            code_verified = False
            status_c = ""
            message = ""

            user = User.objects.get(email=data['email'])

            if user:
                try:
                    code = int(data['code'])
                except ValueError:
                    status_c = False
                    message = "Invalid Code"
                else:
                    if user.reset_password_verify_code(code, confirmed=True):
                        code_verified = True
                    else:
                        status_c = False
                        message = "Failed to reset the password"

                if code_verified:
                    user.set_password(data['password'])
                    user.save()

                    status_c = True
                    message = 'Password Changed'
            else:
                status_c = False
                message = "Could not find user"

            response['status'] = status_c
            if status_c:
                status_code = status.HTTP_200_OK
            else:
                status_code = status.HTTP_200_OK
            response['message'] = message

            return views.Response(response, status=status_code)


# coins feature
class CounterCoinsApiView(views.APIView):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()

    @swagger_auto_schema(auto_schema=None)
    def post(self, request, *args, **kwargs):
        user_detail = get_object_or_404(self.queryset, id=request.user.id)
        redis_cache.hincrby('users:{}:coins'.format(user_detail.id), user_detail.id, 5)
        current_coins = redis_cache.hget('users:{}:coins'.format(user_detail.id), user_detail.id)
        resp_obj = dict(
            status=True,
            total_coins=current_coins,
            message="Coins Added"

        )
        return views.Response(resp_obj, status=status.HTTP_200_OK)


class GetUserCoinsApiView(views.APIView):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    @swagger_auto_schema(auto_schema=None)
    def get(self, request, *args, **kwargs):
        user_detail = get_object_or_404(self.queryset, id=request.user.id)
        coins = redis_cache.hget('users:{}:coins'.format(user_detail.id), user_detail.id)
        resp_obj = dict(
            status=True,
            coins=coins

        )
        return views.Response(resp_obj, status=status.HTTP_200_OK)


class SendEmailNonVerifiedAccount(views.APIView):
    permission_classes = [AllowAny]
    queryset = User.objects.all()

    @swagger_auto_schema(auto_schema=None)
    def post(self, *args, **kwargs):
        user_non_verified_account = User.objects.filter(is_email_verified=False)
        for user_data in user_non_verified_account:
            absolute_url = 'https://' + 'digitvl.com/email-verify/' + str(user_data.email_verification_token)
            email_body = 'Hi ' + user_data.username + \
                         ' Use the link below to verify your email \n' + absolute_url
            data = {'email_body': email_body, 'to_email': user_data.email,
                    'email_subject': 'Verify your email'}

        # send_email_to_non_verify_account(data)

        resp_obj = dict(
            status=True, )
        return views.Response(resp_obj, status=status.HTTP_200_OK)


# send important notification email to the users.
class SendAnnouncementEmail(views.APIView):
    serializer_class = Important_Notification
    permission_classes = [AllowAny]

    queryset = User.objects.all()

    @swagger_auto_schema(auto_schema=None)
    def post(self, request, *args, **kwargs):
        # fetch user email
        serializer = self.serializer_class(data=request.data)

        message = request.data
        for user_data in User.objects.all():
            email_body = message['body']
            data = {'email_body': email_body, 'username': user_data.username, 'to_email': user_data.email,
                    'email_subject': 'Important Announcement'}
            # send_important_announcement.delay(data)

        resp_obj = dict(
            status=True, )
        return views.Response(resp_obj, status=status.HTTP_200_OK)


class GetAllUsersApiView(APIView):
    queryset = User.objects.all()
    serializer_class = GetFullUserSerializer

    def get(self, request):
        users = User.objects.all()
        resp_obj = dict(
            user_data=self.serializer_class(users, context={"request": request}, many=True).data,

        )
        return views.Response(resp_obj, status=status.HTTP_200_OK)


my_login = LoginView.as_view()
