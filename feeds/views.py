from drf_yasg.utils import swagger_auto_schema
from notifications.models import Notification
from rest_framework import status
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny

from accounts import views
from accounts.models import User
from beats.views import StandardResultsSetPagination
from .models import Action
from .serializers import FeedsSerializer, NotificationSerializer, FeaturedSongSerializer


class UserFeeds(ListAPIView):
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    serializer_class = FeedsSerializer
    queryset = Action.objects.all()

    def get(self, request, *args, **kwargs):
        # Display all actions by default
        # actions = self.queryset.exclude(user=self.request.user)

        # following_ids = self.request.user.following.values_list('id', flat=True)
        # if following_ids:
        #     # If user is following others, retrieve only their actions
        #     actions = actions.filter(user_id__in=following_ids)

        actions = self.queryset.select_related('user__profile').prefetch_related('target', 'user__beats',
                                                                           'user__following').exclude(
            verb='featured songs')[:10]

        #
        # for user_actions in actions:
        #     action_users.append(user_actions)

        page = self.pagination_class()
        resp_obj = page.generate_response(actions, FeedsSerializer, request)
        return resp_obj


# current user action
class CurrentUserActionFeeds(ListAPIView):
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    serializer_class = FeedsSerializer
    queryset = Action.objects.all()

    def get(self, request, *args, **kwargs):
        # Display all actions by default
        actions = self.queryset.filter(user=self.request.user)
        actions = actions.select_related('user__profile').prefetch_related('target', 'user__beats',
                                                                           'user__following')[:10]

        page = self.pagination_class()
        resp_obj = page.generate_response(actions, FeedsSerializer, request)
        return resp_obj


class NotificationUnreadListApiView(views.APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    queryset = Notification.objects.all()

    @swagger_auto_schema(operation_description="API For Getting Users Notification. \n\n")
    def get(self, request, *args, **kwargs):
        # get user object
        user = User.objects.get(pk=request.user.id)
        user_notification = user.notifications.unread()
        user_notification_count = user_notification.count()
        resp_obj = dict(
            notification=self.serializer_class(user_notification, context={"request": request}, many=True).data,
            user_notification_count=user_notification_count

        )

        return views.Response(resp_obj, status=status.HTTP_200_OK)


class NotificationReadApiView(views.APIView):
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    queryset = Notification.objects.all()
    schema = None

    def get(self, request, *args, **kwargs):
        # get user object
        user = User.objects.get(pk=request.user.id)
        user_all_notification = user.notifications.all().exclude(actor_object_id=user.id)
        user.notifications.mark_all_as_read(user)
        #
        # resp_obj = dict(
        #     notification=self.serializer_class(user_all_notification, context={"request": request}, many=True).data,
        #     user_notification_mark_as_read=user_notification_mark_as_read
        #
        # )
        page = self.pagination_class()
        resp_obj = page.generate_response(user_all_notification, NotificationSerializer, request)
        return resp_obj
        # return views.Response(resp_obj, status=status.HTTP_200_OK)


class GetFeaturedSongApiView(views.APIView):
    pagination_class = StandardResultsSetPagination
    permission_classes = [AllowAny]
    serializer_class = FeaturedSongSerializer
    queryset = Action.objects.all()

    def get(self, request, *args, **kwargs):
        actions = self.queryset.select_related('user__profile').prefetch_related('target', 'user__beats', ).filter(
            verb='featured songs')[:10]

        page = self.pagination_class()
        resp_obj = page.generate_response(actions, self.serializer_class, request)
        return resp_obj
