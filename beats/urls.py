from django.urls import path
from .views import SongCreate, SongListView, SongUpdate, BeatsLikeView, SongPlayCounterApiView, \
    BeatsDetailApiView, PlayListBeatAddedView, ChildPlaylistView, BeatsSearchEngine, \
    CommentApiView, ChillListApiView, BeatsUserLikesList, SongsRankingPlaysApiView, RandomSongList,\
    RelatedBeatsApiView, ExclusiveSongListView

urlpatterns = [
    # change from songs to beats
    path('beats/update/<int:id>/', SongUpdate.as_view(), name='song-update'),
    path('beats/tags/<str:tags>/', ChillListApiView.as_view(), name='chills-beats'),
    path('beats/comments/<int:beat_id>/', CommentApiView.as_view(), name="comments-detail"),
    path('beats/upload/', SongCreate.as_view(), name='upload-api'),
    path('beats/', SongListView.as_view(), name='songs-api'),
    path('beats/search/', BeatsSearchEngine.as_view(), name='beats-search-engine'),
    path('beats/create/playlist/', ChildPlaylistView.as_view(), name='create-playlist'),
    path('beats/<int:beat_id>/likes/', BeatsLikeView.as_view(), name="beat-likes"),

    path('beats/<str:username_slug>/<str:slug>/', BeatsDetailApiView.as_view(), name="beat-detail"),
    path('beats/users/<str:slug>/<int:beat_id>/added/', PlayListBeatAddedView.as_view(), name="beat-added-playlist"),

    # songs to beats
    path('beats/play/counter/<int:beat_id>/', SongPlayCounterApiView.as_view(), name="song-plays-counter"),
    path('most-plays/songs/', SongsRankingPlaysApiView.as_view(), name="song-ranking"),

    path('users/songs/<str:slug>/likes/list/', BeatsUserLikesList.as_view(), name="users-songs-likes-list"),

    path('random/songs/list/', RandomSongList.as_view(), name='random-song-list'),
    path('related/tracks/<str:slug>/songs/list/', RelatedBeatsApiView.as_view(), name='related-tracks'),
    path('exclusive/songs/', ExclusiveSongListView.as_view(), name='exclusive-songs'),

]
