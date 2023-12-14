# Create your views here.

import redis
from django.conf import settings
from django.db.models import Q
from django.contrib.postgres.search import TrigramSimilarity
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from notifications.signals import notify
from rest_framework import status, response, filters
from rest_framework import (
    views
)
from rest_framework.decorators import permission_classes, api_view
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
# from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from taggit.models import Tag

from accounts.permission import IsOwnerOrReadOnly
from accounts.serializers import ChildFullUserSerializer
from feeds.utils import create_action, delete_action
from .models import Songs, PlayList, Comment
from .permissions import ExclusiveContentPermissionMixin, ExclusiveContentPermission
from .serializers import SongSerializer, AddPlayListSerializer, BeatsUploadSerializer, CommentsSerializer, \
    ChildSongSerializer

# connect to redis
redis_cache = redis.StrictRedis(host=settings.REDIS_HOST,
                                port=settings.REDIS_PORT,
                                db=settings.REDIS_DB)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 8
    page_size_query_param = 'page_size'
    max_page_size = 1000

    def get_next_link(self):
        if not self.page.has_next():
            return None
        page_number = self.page.next_page_number()
        return page_number

    def get_previous_link(self):
        if not self.page.has_previous():
            return None
        page_number = self.page.previous_page_number()
        return page_number

    def generate_response(self, query_set, serializer_obj, request):
        try:
            page_data = self.paginate_queryset(query_set, request)
        except:
            return Response({"error": "No results found for the requested page"}, status=status.HTTP_400_BAD_REQUEST)

        serialized_page = serializer_obj(page_data, context={'request': request}, many=True)
        return self.get_paginated_response(serialized_page.data)


@permission_classes([AllowAny])
class SongListView(ListAPIView):
    pagination_class = StandardResultsSetPagination
    queryset = Songs.objects.select_related('user')
    serializer_class = ChildSongSerializer


# custom search filter
class SongFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        queryset = Songs.objects.annotate(
            similarity=TrigramSimilarity('song_title', request.GET.get["search"]),
        ).filter(similarity__gt=0.1).order_by('-similarity')
        return queryset


# search
@permission_classes([AllowAny])
class BeatsSearchEngine(ListAPIView):
    pagination_class = StandardResultsSetPagination
    queryset = Songs.objects.all()
    serializer_class = SongSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['song_title', 'description', 'tags__name', 'genre', 'user__username']


@permission_classes([IsAuthenticated])
class SongCreate(views.APIView):
    # authentication_classes = [JSONWebTokenAuthentication, ]

    def post(self, request, format=None):
        error_result = {}
        serializer = BeatsUploadSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():

            if self.request.user.membership_plan.volume_remaining <= 0:

                content = {'status': False, 'message': {'limit_error': ["your free uploaded limit is finished"]},
                           'result': error_result}
                return Response(content, status=status.HTTP_200_OK)

            else:
                new_songs = serializer.save(user=self.request.user)
                new_songs.save()
                # update remaining limit of the user when user uploaded the songs.
                # add this on next update
                # remaining_limit = UserMembership.objects.filter(user=request.user).values('volume_remaining')
                output = "Successfully song uploaded"
                content = {'status': True, 'message': output, 'result': serializer.data,
                           }
                # feeds handling
                create_action(request.user, 'posted a song', new_songs, verb_id=1)
                return Response(content, status=status.HTTP_200_OK)
        content = {'status': False, 'message': serializer.errors, 'result': error_result}
        return Response(content, status=status.HTTP_200_OK)


@permission_classes([AllowAny])
class BeatsDetailView(RetrieveAPIView):
    lookup_field = 'slug'
    serializer_class = SongSerializer

    def get_queryset(self, *args, **kwargs):
        return Songs.objects.all()


# view for user song update,
# if user delete the song we have to free the space limit that specific song holds before deleting.

class SongUpdate(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOwnerOrReadOnly]
    lookup_field = 'id'
    parser_class = (FileUploadParser,)
    serializer_class = SongSerializer
    queryset = Songs.objects.all()

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = BeatsUploadSerializer(instance=instance, data=request.data,
                                           partial=True, context={'request': request})  # set partial=True to
        # update a data partially
        if serializer.is_valid():
            serializer.save()
            content = {'status': True, 'message': {"Successfully song updated"}, 'result': serializer.data}
            return Response(content, status=status.HTTP_200_OK)
        else:
            content = {'status': False, 'message': serializer.errors, 'result': {}}
            return Response(content, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            # delete_action(instance, instance.id)
            instance.delete()
            content = {'status': True, 'message': {"Successfully song deleted"}}
            return Response(content, status=status.HTTP_200_OK)
        except Songs.DoesNotExist:
            content = {'status': False, 'message': {"something went wrong"}}
            return Response(content, status=status.HTTP_200_OK)


class BeatsLikeView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, beat_id, format=None):
        beat = get_object_or_404(Songs, id=beat_id)

        if beat.user == request.user:
            resp = {"error": "can_not_like_own_post"}
            return response.Response(resp, status=status.HTTP_200_OK)

        else:
            if Songs.objects.filter(id=beat_id, users_like=request.user):
                beat.users_like.remove(request.user)
                # redis_cache.decr('beat:{}:likes'.format(beat.id))

                resp = {"status": "unliked", "like": False}
            else:
                beat.users_like.add(request.user)
                create_action(request.user, 'like a song', beat, 2)
                notify.send(request.user, recipient=beat.user, verb='liked', target=beat)
                # redis_cache.incr('beat:{}:likes'.format(beat.id))
                # redis_cache.zincrby('beats_ranking', 1, beat.id)
                resp = {"status": "liked", "like": True}

            return response.Response(resp, status=status.HTTP_200_OK)


class ChildPlaylistView(views.APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddPlayListSerializer

    # create_serializer_class = CreateInviteBrandSerializer

    def get(self, request, *args, **kwargs):
        playlist = PlayList.objects.filter(owner=request.user)
        resp_obj = dict(
            playlist=self.serializer_class(playlist, context={"request": request}, many=True).data,

        )
        return views.Response(resp_obj, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        error_result = {}
        serializer = AddPlayListSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=self.request.user)
            output = "Successfully playlist added"
            content = {'status': True, 'message': output, 'result': serializer.data}
            return Response(content, status=status.HTTP_200_OK)
        content = {'status': False, 'message': serializer.errors, 'result': error_result}
        return Response(content, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def PlayListBeatAdded(request, slug, beat_id):
    try:
        playlist = get_object_or_404(PlayList.objects.all(), slug=slug, owner=request.user)
        playlist.beats.add(beat_id)
        content = {'message': 'Successfully beat added'}

        return Response(content, status=status.HTTP_200_OK)
    except Exception as e:
        return views.Response({"error": "Something went wrong"}, status=status.HTTP_200_OK)


class ChildPlaylistView(views.APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddPlayListSerializer

    # create_serializer_class = CreateInviteBrandSerializer

    def get(self, request, *args, **kwargs):
        playlist = PlayList.objects.filter(owner=request.user)
        resp_obj = dict(
            playlist=self.serializer_class(playlist, context={"request": request}, many=True).data,

        )
        return views.Response(resp_obj, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        error_result = {}
        serializer = AddPlayListSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=self.request.user)
            output = "Successfully playlist added"
            content = {'status': True, 'message': output, 'result': serializer.data}
            return Response(content, status=status.HTTP_200_OK)
        content = {'status': False, 'message': serializer.errors, 'result': error_result}
        return Response(content, status=status.HTTP_200_OK)


class CommentApiView(views.APIView):
    pagination_class = StandardResultsSetPagination
    permission_classes = [AllowAny]
    serializer_class = CommentsSerializer

    def get(self, request, beat_id, *args, **kwargs):
        comments_list = Comment.objects.select_related('beats', 'beats__user', 'commenter__profile').filter(
            beats=beat_id)
        page = self.pagination_class()
        resp_obj = page.generate_response(comments_list, CommentsSerializer, request)
        return resp_obj

    def post(self, request, beat_id):
        try:
            input_data = dict()
            # input_data['beats'] = beat_id
            beat_object = get_object_or_404(Songs, id=beat_id)
            input_data['commenter'] = self.request.user
            input_data['body'] = request.data.get('body')
            if input_data['body'] is not None:
                comments = Comment.objects.create(beats=beat_object, commenter=input_data['commenter'],
                                                  body=input_data['body'])
                # serializer = self.serializer_class(data=comments)
                if comments:
                    resp = self.serializer_class(comments, context={"request": request}).data
                    create_action(request.user, 'added a comment on', beat_object, 3)
                    notify.send(request.user, recipient=beat_object.user, verb='commented on', target=beat_object)
                    return views.Response({'status': True, "message": "comment added", 'result': resp},
                                          status=status.HTTP_200_OK)
                else:
                    return views.Response({'status': False, "message": "field may not be null", 'result': {}},
                                          status=status.HTTP_200_OK)

            else:
                return views.Response({'status': False, "message": "field may not be null", 'result': {}},
                                      status=status.HTTP_200_OK)

        except Comment.DoesNotExist:
            return Response({'status': False, "message": "Beat does not exists", 'result': {}},
                            status=status.HTTP_200_OK)


class BeatsDetailApiView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = SongSerializer

    def get(self, request, slug, *args, **kwargs):
        beats_detail = get_object_or_404(Songs, slug__iexact=slug)
        resp_obj = dict(
            beats_detail=self.serializer_class(beats_detail, context={"request": request}).data)
        return views.Response(resp_obj, status=status.HTTP_200_OK)


# trending Api
class ChillListApiView(views.APIView):
    pagination_class = StandardResultsSetPagination
    permission_classes = [AllowAny]
    serializer_class = SongSerializer

    def get(self, request, tags, *args, **kwargs):
        object_list = Songs.objects.all()
        tag = get_object_or_404(Tag, name=tags)
        beats_list = object_list.filter(tags__in=[tag])
        page = self.pagination_class()
        resp_obj = page.generate_response(beats_list, self.serializer_class, request)
        return resp_obj


class SongPlayCounterApiView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = SongSerializer

    def post(self, request, beat_id, *args, **kwargs):
        beats_detail = get_object_or_404(Songs, id=beat_id)
        redis_cache.incr('beat:{}:plays'.format(beats_detail.id))
        redis_cache.zincrby('plays_ranking', 1, beats_detail.id)
        resp_obj = dict(
            beats_detail=self.serializer_class(beats_detail, context={"request": request}).data,

        )
        return views.Response(resp_obj, status=status.HTTP_200_OK)


"""
Songs Ranking with most songs plays, but in future we do with most likes and most comment recommendation 
"""


class SongsRankingPlaysApiView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = SongSerializer

    def get(self, request, *args, **kwargs):
        # get songs ranking dictionary
        plays_ranking = redis_cache.zrange('plays_ranking', 0, -1, desc=True)[:15]
        plays_ranking_ids = [int(id) for id in plays_ranking]
        # get most viewed images
        most_played = list(Songs.objects.filter(id__in=plays_ranking_ids))
        most_played.sort(key=lambda x: plays_ranking_ids.index(x.id))

        resp_obj = dict(
            beats_detail=self.serializer_class(most_played, context={"request": request}, many=True).data,

        )
        return views.Response(resp_obj, status=status.HTTP_200_OK)


# list of all users that like specific songs
class BeatsUserLikesList(views.APIView):
    pagination_class = StandardResultsSetPagination
    serializer_class = ChildFullUserSerializer
    queryset = Songs.objects.all()

    def get(self, request, slug, *args, **kwargs):
        users_like_list = []
        current_beat = get_object_or_404(Songs, slug=slug)
        users_like = current_beat.users_like.all()
        for users_like_ids in users_like:
            users_like_list.append(users_like_ids)

        page = self.pagination_class()
        resp_obj = page.generate_response(users_like_list, ChildFullUserSerializer, request)
        return resp_obj


# Random Songs List
class RandomSongList(views.APIView):
    serializer_class = ChildSongSerializer
    queryset = Songs.objects.select_related('user')

    def get(self, request, *args, **kwargs):
        songs_by_tags = self.queryset.all().order_by('?')[:50]
        resp_obj = dict(
            random_song_list=self.serializer_class(songs_by_tags, context={"request": request}, many=True).data,

        )
        return views.Response(resp_obj, status=status.HTTP_200_OK)


# related tracks for detail page
class RelatedBeatsApiView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = ChildSongSerializer
    queryset = Songs.objects.select_related('user')

    def get(self, request, slug, *args, **kwargs):
        song = get_object_or_404(Songs, slug__iexact=slug)
        songs_by_tags = self.queryset.filter(Q(genre=song.genre) | Q(genre='love')).order_by('?')[:3]
        resp_obj = dict(
            related_song_list=self.serializer_class(songs_by_tags, context={"request": request}, many=True).data,

        )
        return views.Response(resp_obj, status=status.HTTP_200_OK)


# Exclusive Content
@permission_classes([IsAuthenticated, ExclusiveContentPermission])
class ExclusiveSongListView(ListAPIView):
    pagination_class = StandardResultsSetPagination
    queryset = Songs.objects.select_related('user').filter(exclusive_content=2)
    # queryset = Songs.objects.select_related('user')
    serializer_class = ChildSongSerializer
