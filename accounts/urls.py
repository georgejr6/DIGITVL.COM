from django.urls import path

from .views import ProfileUpdateAPIView, UserList, LogoutView, CurrentUserApiView, my_login, VerifyEmail, \
    ResetPasswordRequestView, ResetPasswordView, CounterCoinsApiView, GetUserCoinsApiView, SendEmailNonVerifiedAccount, \
    SendAnnouncementEmail, GetAllUsersApiView

urlpatterns = [
    path('account/create/', UserList.as_view()),
    path('account/login/', my_login, name='login'),
    path('account/logout/', LogoutView.as_view(), name='logout'),
    path('account/profile/update/<int:user_id>/', ProfileUpdateAPIView.as_view(), name='profile'),
    path('account/current-user/', CurrentUserApiView.as_view(), name='current-user'),
    path('account/email-verify/', VerifyEmail.as_view(), name="email-verify"),

    path('account/forget-password/request/', ResetPasswordRequestView.as_view(), name='reset-password-request'),
    path('account/new/forget-password/', ResetPasswordView.as_view(), name='reset-password'),

    path('account/CounterCoins/', CounterCoinsApiView.as_view(), name='coins'),
    path('account/GetCoins/', GetUserCoinsApiView.as_view(), name='get-coins'),

    path('account/send/email/unverified/', SendEmailNonVerifiedAccount.as_view(), name='non-verified-account'),

    path('send/announcement/', SendAnnouncementEmail.as_view(), name='send-announcement'),
    path('users-data/', GetAllUsersApiView.as_view(), name='user-data')

]
