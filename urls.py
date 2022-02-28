from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.league_login, name='league_login'),
    path('logout/', views.league_logout, name='league_logout'),
    path('scoreboard/', views.scoreboard, name='scoreboard'),
    path('round/<int:season_pk>/<int:round>/', views.round, name='round'),
    path('player/<int:pk>/', views.player, name='player'),
    path('team/<int:pk>/', views.team, name='players'),
    path('team/<int:pk>/', views.team, name='team'),
    path('team/percentile/<int:team_id>/<int:percentile>/', 
          views.team_percentile, name='team_percentile'),
    path('game/<int:pk>/', views.game, name='game'),
    path('stats/', views.stats, name='stats'),
]

