import mutagen
import redis
from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import UploadedFile
from django.db import models
from django.db.models.signals import m2m_changed, pre_save, pre_delete, post_delete
from django.dispatch import receiver
from easy_thumbnails.fields import ThumbnailerImageField
from rest_framework.reverse import reverse as api_reverse
from sortedm2m.fields import SortedManyToManyField
from taggit.managers import TaggableManager

from beats.utils import get_unique_slug
from feeds.models import Action
from subscriptions.models import UserMembership
from .validators import (
    FileExtensionValidator
)

# redis setting
redis_cache = redis.StrictRedis(host=settings.REDIS_HOST,
                                port=settings.REDIS_PORT,
                                db=settings.REDIS_DB)


class Songs(models.Model):
    class ContentTypeChoices(models.IntegerChoices):
        FREE = 1, "free"
        EXCLUSIVE = 2, "paid members"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='beats', on_delete=models.CASCADE)
    slug = models.SlugField(max_length=200, db_index=True)
    song_title = models.CharField(max_length=250)
    genre = models.CharField(max_length=100, blank=True)
    tags = TaggableManager()
    description = models.CharField(max_length=300)
    store_link = models.URLField(null=True, blank=True)
    photo_main = ThumbnailerImageField(upload_to='photos/%Y/%m/%d/', resize_source=dict(size=(250, 250), sharpen=True))
    audio_file = models.FileField(upload_to='songs/%Y/%m/%d/')
    duration_seconds = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    users_like = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                        related_name='beats_liked',
                                        blank=True)
    total_likes = models.PositiveIntegerField(db_index=True,
                                              default=0)
    exclusive_content = models.PositiveSmallIntegerField(choices=ContentTypeChoices.choices,
                                                         default=ContentTypeChoices.FREE)

    def __str__(self):
        return self.song_title

    def save(self, *args, **kwargs):
        if not self.slug:
            slug_str = f'{self.song_title}'
            self.slug = get_unique_slug(self, slug_str, Songs.objects)
            # if self.photo_main:

        super().save(*args, **kwargs)

    def get_api_url(self, request=None):
        return api_reverse('beat-detail', kwargs={'username_slug': self.user.username_slug, 'slug': self.slug},
                           request=request)

    @property
    def get_slug(self):
        return self.slug

    @property
    def username(self):
        return self.user.username

    @property
    def username_slug(self):
        return self.user.username_slug

    @property
    def limit_remaining(self):
        return self.user.membership_plan.volume_remaining

    @property
    def get_subscription_badge(self):
        return self.user.membership_plan.subscription_badge

    @property
    def plays_count(self):
        return redis_cache.get('beat:{}:plays'.format(self.id))

    class Meta:
        ordering = ('-created_at',)
        index_together = (('id', 'slug'),)


@receiver(m2m_changed, sender=Songs.users_like.through)
def users_like_changed(sender, instance, **kwargs):
    instance.total_likes = instance.users_like.count()
    instance.save()


@receiver(pre_save, sender=Songs)
def file_duration(sender, instance, raw, using, update_fields, **kwargs):
    file_was_updated = False
    if hasattr(instance.audio_file, 'file') and isinstance(instance.audio_file.file, UploadedFile):
        file_was_updated = True

    if update_fields and "audio_file" in update_fields:
        file_was_updated = True

    if file_was_updated:
        # read audio file metadata
        audio_info = mutagen.File(instance.audio_file).info
        # set audio duration in seconds, so we can access it in database
        instance.duration_seconds = int(audio_info.length)
        try:
            volume_remaining = instance.user.membership_plan.volume_remaining - instance.duration_seconds
            if volume_remaining:
                UserMembership.objects.filter(user=instance.user).update(volume_remaining=volume_remaining)
            else:
                pass
        except:
            pass
        print(">> audio duration was was updated")

    else:
        print(">> file not changed - duration was NOT updated")


class PlayList(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, null=True, blank=True, db_index=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='playlist', on_delete=models.CASCADE)
    beats = SortedManyToManyField(Songs, related_name='playlist_beats')
    is_private = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created',)

    def save(self, *args, **kwargs):
        if not self.slug:
            slug_str = f'{self.name}'
            self.slug = get_unique_slug(self, slug_str, PlayList.objects)

        super().save(*args, **kwargs)

    def playlist_cover_photo(self, request):
        try:
            playlist_cover = self.beats.first()
            playlist_cover = request.build_absolute_uri(playlist_cover.photo_main.url)
            return playlist_cover
        except Exception:
            return None

    @property
    def beats_count(self):
        return self.beats.count()


class Comment(models.Model):
    beats = models.ForeignKey(Songs,
                              on_delete=models.CASCADE,
                              related_name='comments')
    commenter = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='user_comments', on_delete=models.CASCADE)
    body = models.TextField(max_length=250)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ('-created',)

    @property
    def get_subscription_badge(self):
        return self.user.membership_plan.subscription_badge

    @property
    def username_slug(self):
        return self.user.username_slug

    def __str__(self):
        return 'Comment by {} on {}'.format(self.commenter.username, self.beats)


@receiver(pre_delete, sender=Songs)
def delete_song(sender, instance, **kwargs):
    try:
        free_up_limit = instance.duration_seconds
        user = instance.user
        limit = UserMembership.objects.filter(user=user).values_list('volume_remaining', flat=True)[0]
        update_space = limit + free_up_limit
        UserMembership.objects.filter(user=instance.user).update(volume_remaining=update_space)
        print("updated")
    except Songs.DoesNotExist:
        print("error")


# using this signal to delete the songs from the feeds and their action
@receiver(post_delete, sender=Songs)
def delete_action(sender, instance, **kwargs):
    # delete action from feed table
    target_ct = ContentType.objects.get_for_model(instance)
    delete_all_actions_target_null = Action.objects.filter(target_ct=target_ct, target_id=instance.id)

    delete_all_actions_target_null.delete()
