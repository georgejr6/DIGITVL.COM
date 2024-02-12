from django.urls import path
from . import views

urlpatterns = [
    # other user urls
    path('profile/<str:username_slug>/detail/', views.UserProfileDetail.as_view(), name='profile-detail'),
    path('profile/<str:username_slug>/tracks/', views.UserProfileBeatsView.as_view(), name='profile-beats'),
    path('profile/<str:username_slug>/playlist/<str:slug>/detail/', views.PlaylistDetailView.as_view(),
         name='profile-playlist-detail'),
    path('profile/<str:username_slug>/playlist/', views.UserProfilePlaylistView.as_view(), name='profile-playlist'),

    # current user urls
    path('you/library/tracks/', views.CurrentUserBeats.as_view(), name='you-library-tracks'),
    path('you/library/likes/', views.UserlikeDetail.as_view(), name='you-library-like'),
    path('you/library/playlist/', views.PlaylistView.as_view(), name="you-library-playlist"),

    path('profile/<int:pk>/follow/', views.FollowUserView.as_view(), name="follow-user"),
    path('profile/<str:username_slug>/follower/list/', views.ListFollowersView.as_view(), name="follower-list"),
    path('profile/<str:username_slug>/following/list/', views.ListFollowingView.as_view(), name="following-list"),

    path('suggestions/<str:username_slug>/who-to-follow/list/', views.WhoToFollowList.as_view(), name="who-to-follow"),

    path('check/<str:username_slug>/follow/status/', views.FollowedStatusView.as_view(), name="check-follow-status"),

    # playlist song deleted
    path('you/library/playlist/<str:slug>/delete/song/<int:song_id>/', views.PlaylistSongsDeleteView.as_view(),
         name="playlist-song-deleted"),

    path('you/library/delete/playlist/<str:slug>/', views.PlaylistDeleteView.as_view(), name="playlist-deleted"),

    # library recently searched songs
    path('your/library/recently-searched/', views.RecentlySearchedSongsAPIView.as_view(), name='recently-searched'),
    path('your/library/recently/listened/', views.RecentlyPlayedSongsAPIView.as_view(), name='recently-listened'),
]
