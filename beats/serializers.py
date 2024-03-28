import json
import redis
import six
from django.conf import settings
from drf_yasg.inspectors import FieldInspector
from rest_framework import serializers
from taggit.serializers import (TagListSerializerField,
                                TaggitSerializer)

from .models import Songs, PlayList, Comment
from .validators import (
    FileExtensionValidator
)

# connect to redis
redis_cache = redis.StrictRedis(host=settings.REDIS_HOST,
                                port=settings.REDIS_PORT,
                                db=settings.REDIS_DB)


class NewTagListSerializerField(TagListSerializerField):
    def to_internal_value(self, value):
        if isinstance(value, six.string_types):
            if not value:
                value = "[]"
            try:
                if type(value) == str:
                    if value.__contains__('"'):
                        value = json.loads(value)
                    else:
                        value = value.split(',')

            except ValueError:
                self.fail('invalid_json')

        if not isinstance(value, list):
            self.fail('not_a_list', input_type=type(value).__name__)

        for s in value:
            if not isinstance(s, six.string_types):
                self.fail('not_a_str')

            self.child.run_validation(s)

        return value


class BeatsUploadSerializer(TaggitSerializer, serializers.ModelSerializer):
    slug = serializers.SerializerMethodField()
    tags = NewTagListSerializerField()
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    photo_main = serializers.ImageField(required=True)
    audio_file = serializers.FileField(required=True)

    class Meta:
        model = Songs
        fields = ['id', 'slug', 'song_title', 'user', 'genre', 'tags', 'description', 'store_link', 'photo_main',
                  'audio_file',
                  'username', 'limit_remaining', 'get_subscription_badge', 'exclusive_content']

    # def __init__(self, user, *args, **kwargs):
    #     super(BeatsUploadSerializer, self).__init__(*args, **kwargs)
    #     super().__init__(**kwargs)
    #     self.fields["audio_file"].validators.append(FileExtensionValidator('audio', user))
    #     self.fields["photo_main"].validators.append(FileExtensionValidator('image', user))

    def get_slug(self, obj):
        return obj.slug


class SongSerializer(TaggitSerializer, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    tags = NewTagListSerializerField()
    user_like = serializers.SerializerMethodField()
    # photo_main = serializers.ImageField(required=True, validators=[FileExtensionValidator('image')])
    # audio_file = serializers.FileField(required=True, validators=[FileExtensionValidator('audio')])
    url = serializers.SerializerMethodField()

    class Meta:
        model = Songs
        fields = ['id', 'slug', 'song_title', 'genre', 'tags', 'description', 'store_link', 'photo_main', 'audio_file',
                  'user_like', 'total_likes', 'plays_count',
                  'url', 'username', 'username_slug', 'get_subscription_badge', 'exclusive_content']

    def get_user_like(self, obj):
        request = self.context.get("request")
        if request.user.id:
            return Songs.objects.filter(id=obj.id, users_like=request.user.id).exists()
        else:
            return False

    def get_url(self, obj):
        # request added to get complete "http://127.0.0.1:8000/api/songs/update/11"
        request = self.context.get("request")
        return obj.get_api_url(request=request)


class ChildSongSerializer(serializers.ModelSerializer):
    user_like = serializers.SerializerMethodField()

    class Meta:
        model = Songs
        fields = ['id', 'slug', 'song_title', 'description', 'total_likes', 'photo_main', 'audio_file',
                  'username', 'username_slug', 'get_subscription_badge', 'exclusive_content', 'user_like']

    def get_user_like(self, obj):
        request = self.context.get("request")
        if request.user.id:
            return Songs.objects.filter(id=obj.id, users_like=request.user.id).exists()
        else:
            return False


class AddPlayListSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    slug = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PlayList
        fields = ['id', 'slug', 'name', 'is_private', 'beats_count']

    def get_slug(self, obj):
        return obj.slug


class UserPlayListSerializer(serializers.ModelSerializer):
    beats = ChildSongSerializer(many=True, read_only=True)
    cover_pic = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PlayList
        fields = ['id', 'slug', 'name', 'beats', 'is_private', 'beats_count', 'cover_pic']

    def get_cover_pic(self, obj):
        request = self.context.get("request")
        playlist_cover = obj.beats.first()
        if playlist_cover:
            return request.build_absolute_uri(playlist_cover.photo_main.url)
        else:
            return None

class CommentsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    beats = ChildSongSerializer(read_only=True)
    username = serializers.SerializerMethodField(read_only=True)
    profile_pic = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'beats', 'body', 'username', 'profile_pic', 'get_subscription_badge']

    def get_username(self, obj):
        return obj.commenter.username


    def get_profile_pic(self, obj):
        request = self.context.get("request")
        if request and obj.commenter.profile.avatar:
            return request.build_absolute_uri(obj.commenter.profile.avatar.url)
        else:
            return None

        # Override get_schema_fields to hide read-only fields from schema