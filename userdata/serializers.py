# serializers.py

from rest_framework import serializers

from accounts.serializers import ChildFullUserSerializer
from beats.serializers import ChildSongSerializer
from .models import ListenedSong, SearchedSong

class RecentlyListenedSongSerializer(serializers.ModelSerializer):
    user = ChildFullUserSerializer(read_only=True)
    song = ChildSongSerializer(read_only=True)
    class Meta:
        model = ListenedSong
        fields = '__all__'

class SearchedSongSerializer(serializers.ModelSerializer):
    user =  ChildFullUserSerializer(read_only=True)
    song = ChildSongSerializer(read_only=True)
    class Meta:
        model = SearchedSong
        fields = '__all__'
