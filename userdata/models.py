from django.conf import settings
from django.db import models

# Create your models here.
from datetime import timedelta
from django.utils import timezone

from beats.models import Songs



class ListenedSongManager(models.Manager):

    def recent_for_user(self, user, days=7):
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(user=user, listened_at__gte=cutoff_date).order_by('-listened_at')

class ListenedSong(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    song = models.ForeignKey(Songs, on_delete=models.CASCADE)
    listened_at = models.DateTimeField(auto_now_add=True)

    objects = ListenedSongManager()
    class Meta:
        verbose_name ='Recently Listen Song'
        verbose_name_plural = 'Recently Listen Songs'




class SearchedSongManager(models.Manager):

    def recent_for_user(self, user, days=7):
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(user=user, searched_at__gte=cutoff_date).order_by('-searched_at')
class SearchedSong(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    song = models.ForeignKey(Songs, on_delete=models.CASCADE)
    searched_at = models.DateTimeField(auto_now_add=True)
    objects = SearchedSongManager()
