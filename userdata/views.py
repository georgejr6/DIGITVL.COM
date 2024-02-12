# Create your views here.

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import views, status
from rest_framework.generics import ListAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from accounts.models import Profile, User, Contact
from accounts.serializers import ProfileSerializer, ChildFullUserSerializer
from beats.models import Songs, PlayList
from beats.permissions import IsPlaylistUserOrReadOnly, IsPlaylistObjectPermissionUserOrReadOnly
from beats.serializers import ChildSongSerializer, UserPlayListSerializer
from beats.views import StandardResultsSetPagination
from notifications.signals import notify

from userdata.models import ListenedSong, SearchedSong
from userdata.serializers import RecentlyListenedSongSerializer, SearchedSongSerializer


class UserProfileDetail(views.APIView):
    serializer_class = ProfileSerializer
    permission_classes = [AllowAny]
    queryset = Profile.objects.select_related('user').all()

    def get(self, request, *args, **kwargs):
        username_slug = kwargs.get('username_slug')
        try:
            profile_detail = get_object_or_404(self.queryset, user__username_slug__iexact=username_slug)
            resp_obj = dict(
                profile_detail=self.serializer_class(profile_detail, context={
                    'request': request}).data

            )
            return views.Response(resp_obj, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            return views.Response({"status": False, "message": "Something went wrong"}, status=status.HTTP_200_OK)


class UserProfileBeatsView(views.APIView):
    pagination_class = StandardResultsSetPagination
    queryset = Songs.objects.all()

    def get(self, request, *args, **kwargs):
        username_slug = kwargs.get('username_slug')
        try:
            tracks = self.queryset.filter(user__username_slug__iexact=username_slug)
            page = self.pagination_class()
            resp_obj = page.generate_response(tracks, ChildSongSerializer, request)
            return resp_obj
        except Exception as e:
            return views.Response({"status": False, "message": "Something went wrong"}, status=status.HTTP_200_OK)


class UserProfilePlaylistView(views.APIView):
    pagination_class = StandardResultsSetPagination
    serializer_class = UserPlayListSerializer
    queryset = PlayList.objects.all()

    def get(self, request, *args, **kwargs):
        username_slug = kwargs.get('username_slug')
        try:
            playlist = self.queryset.filter(owner__username_slug__iexact=username_slug, is_private=False)
            page = self.pagination_class()
            resp_obj = page.generate_response(playlist, self.serializer_class, request)
            return resp_obj

        except Exception as e:
            return views.Response({"status": False, "message": "Something went wrong"}, status=status.HTTP_200_OK)


# <!------ current user profile page ------------!->
# current user library
class CurrentUserBeats(ListAPIView):
    pagination_class = StandardResultsSetPagination
    queryset = Songs.objects.all()
    serializer_class = ChildSongSerializer

    def get_queryset(self, *args, **kwargs):
        return Songs.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.pagination_class()
        resp_obj = page.generate_response(queryset, ChildSongSerializer, request)
        return resp_obj


# current user like details
class UserlikeDetail(ListAPIView):
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    serializer_class = ChildSongSerializer

    def get_queryset(self, *args, **kwargs):
        return Songs.objects.filter(users_like=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.pagination_class()
        resp_obj = page.generate_response(queryset, ChildSongSerializer, request)
        return resp_obj


# for current user

class PlaylistView(views.APIView):
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        queryset = PlayList.objects.filter(owner=request.user)
        page = self.pagination_class()
        resp_obj = page.generate_response(queryset, UserPlayListSerializer, request)
        return resp_obj


# for other users
class PlaylistDetailView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = UserPlayListSerializer
    queryset = PlayList.objects.all()

    def get(self, request, slug, *args, **kwargs):
        username_slug = kwargs.get('username_slug')
        playlist = self.queryset.filter(slug=slug, owner__username_slug=username_slug)
        resp_obj = dict(
            playlist=self.serializer_class(playlist, context={"request": request}, many=True).data,

        )

        return views.Response(resp_obj, status=status.HTTP_200_OK)


# current user playlist songs delete
class PlaylistSongsDeleteView(views.APIView):
    # change this to is owner Permission
    permission_classes = [IsPlaylistUserOrReadOnly]
    serializer_class = UserPlayListSerializer
    queryset = PlayList.objects.all()

    def post(self, request, slug, song_id, *args, **kwargs):
        playlist = get_object_or_404(self.queryset, slug=slug)
        # getting song object which song want to delete from the playlist
        song_object = get_object_or_404(Songs, id=song_id)
        if playlist.owner == request.user:
            # # pass the song object to m2m relation
            playlist.beats.remove(song_object)
            resp_obj = dict(
                status="True", message="song deleted"
            )

            return views.Response(resp_obj, status=status.HTTP_200_OK)
        else:
            resp_obj = dict(
                status="False", message="permission denied"
            )
            return views.Response(resp_obj, status=status.HTTP_200_OK)


# view for to delete the playlist
class PlaylistDeleteView(DestroyAPIView):
    permission_classes = [IsPlaylistObjectPermissionUserOrReadOnly]
    serializer_class = UserPlayListSerializer
    lookup_field = 'slug'
    queryset = PlayList.objects.all()

    def delete(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.delete()
            content = {'status': True, 'message': {"Successfully playlist deleted"}}
            return Response(content, status=status.HTTP_200_OK)
        except PlayList.DoesNotExist:
            content = {'status': False, 'message': {"something went wrong"}}
            return Response(content, status=status.HTTP_200_OK)


# followers and following code
class FollowUserView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        response = dict()

        to_follow_id = kwargs.get('pk')

        try:
            to_follow = User.objects.get(id=to_follow_id)
        except User.DoesNotExist:
            return Response({'status': False, "message": "User with this id does not exist", 'result': {}},
                            status=status.HTTP_200_OK)

        if request.user == to_follow:
            return Response({'status': False, "message": "Can not follow yourself", 'result': {}},
                            status=status.HTTP_200_OK)

        # if request.user.following(to_follow):
        if Contact.objects.filter(user_from=request.user, user_to=to_follow).exists():
            try:
                Contact.objects.filter(user_from=request.user,
                                       user_to=to_follow).delete()
                response['status'] = True
                response['message'] = "unfollowed"
                response['user'] = ChildFullUserSerializer(request.user, context={'request': request}).data
            except User.DoesNotExist:
                response['status'] = False
                response['error'] = 'Something went wrong'
        else:
            obj_id = Contact.objects.get_or_create(
                user_from=request.user,
                user_to=to_follow)
            notify.send(request.user, recipient=to_follow, verb='follows', target=to_follow)
            # notify.send(request.user, recipient=to_follow, verb='follows')
            # notification.add_follow(request.user.id, to_follow.id, obj_id, datetime.utcnow())
            response['status'] = True
            response['message'] = "followed"
            response['user'] = ChildFullUserSerializer(request.user, context={'request': request}).data

        return views.Response(response, status.HTTP_200_OK)


class ListFollowingView(views.APIView):
    pagination_class = StandardResultsSetPagination
    permission_classes = [AllowAny]
    serializer_class = ChildFullUserSerializer

    def get(self, request, *args, **kwargs):
        username_slug = kwargs.get('username_slug')
        user = get_object_or_404(User, username_slug=username_slug)
        following_list = []
        following = user.following.all()

        for f in following:
            following_list.append(f)

        page = self.pagination_class()
        resp_obj = page.generate_response(following_list, ChildFullUserSerializer, request)
        return resp_obj


class ListFollowersView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = ChildFullUserSerializer
    pagination_class = StandardResultsSetPagination

    def get(self, request, *args, **kwargs):
        username_slug = kwargs.get('username_slug')

        user = get_object_or_404(User, username_slug=username_slug)

        followers_list = []
        followers = user.followers.all()

        for f in followers:
            followers_list.append(f)

        page = self.pagination_class()
        resp_obj = page.generate_response(followers_list, ChildFullUserSerializer, request)
        # profile_detail = self.serializer_class(resp_obj, context={'request': request}).data
        return resp_obj


class WhoToFollowList(views.APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChildFullUserSerializer
    queryset = User.objects.only('id', 'username', 'username_slug')

    def get(self, request, *args, **kwargs):
        username_slug = kwargs.get('username_slug')
        try:
            current_user = self.queryset.get(username_slug=username_slug)
            # recommended_user = User.objects.values_list('id', flat=True).exclude(username=current_user)
        except User.DoesNotExist:
            return Response({'status': False, "message": "User with this id does not exist", 'result': {}},
                            status=status.HTTP_200_OK)

        following_list = []
        mutual_following_list = []
        # fetch current user following by using order by
        current_user_following_ids = current_user.following.values_list('id', flat=True).order_by('?')[:10]
        all_users = self.queryset.values_list('id', flat=True).exclude(id__in=current_user_following_ids).order_by('?')[
                    :10]

        if not current_user_following_ids:
            mutual_following_list.append(
                self.queryset.values_list('id', flat=True).exclude(username=current_user).order_by('?')[:3])
            recommended_list = User.objects.filter(id__in=mutual_following_list)
        else:
            for other_ids in current_user_following_ids:
                user = self.queryset.get(id=other_ids)
                mutual_following_list.append(user.following.values_list('id', flat=True).exclude(username=current_user))

            if len(mutual_following_list) <= 2:
                mutual_following_list.append(self.queryset.values_list('id', flat=True).exclude(
                    Q(id__in=current_user_following_ids) and Q(username=current_user)).order_by('?')[:3])

            # set comprehension to remove the duplicates lists
            recommended_set = {item for sublist in mutual_following_list for item in sublist if
                               item not in current_user_following_ids}

            recommended_list = self.queryset.filter(id__in=recommended_set).order_by('?')[:3]
        # random_ids = random.sample(recommended_list, 3)

        for f in recommended_list:
            following_list.append(self.serializer_class(f, context={'request': request}).data)

        return views.Response({"status": True, "message": "Success", "result": following_list})


class FollowedStatusView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, username_slug, *args, **kwargs):
        try:
            user = User.objects.get(username_slug=username_slug)
            if Contact.objects.filter(user_from=self.request.user, user_to=user).exists():
                followed = True
            else:
                followed = False

        except User.DoesNotExist:
            return views.Response({"status": False, "message": "no user found"}, status=status.HTTP_200_OK)

        return views.Response({"status": True, "message": "Success", "followed": followed})

class RecentlyPlayedSongsAPIView(views.APIView):
    pagination_class = StandardResultsSetPagination
    serializer_class = RecentlyListenedSongSerializer
    model = ListenedSong
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        user = self.request.user
        queryset = self.model.objects.recent_for_user(user)
        page = self.pagination_class()
        resp_obj = page.generate_response(queryset, SearchedSongSerializer, request)
        return resp_obj
    def post(self, request, *args, **kwargs):
        user = request.user

        song_slug = request.data.get('song_slug')
        try:
            song = Songs.objects.get(slug=song_slug)

            # Check if the recent song already exists for the user
            if self.model.objects.filter(user=user, song=song).exists():
                return self.error_response("This song is already in your recently listen history.")

            self.model.objects.get_or_create(user=user, song=song)
            return self.success_response("song added in recently playing history")
        except Songs.DoesNotExist:
            return self.error_response("Song not found.")
    def success_response(self, message):
        return Response({'status': 'True', 'message': message}, status=status.HTTP_200_OK)

    def error_response(self, message):
        return Response({'status': 'False', 'message': message}, status=status.HTTP_200_OK)



class RecentlySearchedSongsAPIView(views.APIView):
    pagination_class = StandardResultsSetPagination
    serializer_class = SearchedSongSerializer
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        user = self.request.user
        queryset = SearchedSong.objects.recent_for_user(user)
        page = self.pagination_class()
        resp_obj = page.generate_response(queryset, SearchedSongSerializer, request)
        return resp_obj
    def post(self, request, *args, **kwargs):
        user = request.user

        song_slug = request.data.get('song_slug')
        try:
            song = Songs.objects.get(slug=song_slug)

            # Check if the searched song already exists for the user
            if SearchedSong.objects.filter(user=user, song=song).exists():
                return self.error_response("This song is already in your search history.")

            searched_song = SearchedSong.objects.create(user=user, song=song)
            return self.success_response("Searched song added in history.")
        except Songs.DoesNotExist:
            return self.error_response("Song not found.")
    def success_response(self, message):
        return Response({'status': 'True', 'message': message}, status=status.HTTP_200_OK)

    def error_response(self, message):
        return Response({'status': 'False', 'message': message}, status=status.HTTP_200_OK)