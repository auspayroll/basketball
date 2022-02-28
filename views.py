import datetime
from django.utils import timezone
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from .models import Player, Team, Season, Game, Profile
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages


def league_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password  = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                user.profile.login_count += 1
                user.profile.save()
                return redirect('scoreboard')
            messages.error(request, 'Invalid Login')
    else:
        form = AuthenticationForm(request)
    return render(request, 'registration/login.html', { 'form': form })  

@login_required
def league_logout(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.profile.last_logout = timezone.now()
        user.profile.total_seconds = (user.profile.last_logout - user.last_login).seconds
        user.profile.save()
        return redirect('league_login') 

@permission_required('league.view_player')
def player(request, pk):
    player = get_object_or_404(Player, pk=pk)
    if request.user.has_perm('league.change_player') or \
        request.user.profile.team_id == player.team_id:
        return render(request, 'players/player.html', {'player': player, 'subtitle': player })
    else:
        return HttpResponse('Unauthorized', status=401) 

@permission_required('league.view_team')
def team_percentile(request, team_id, percentile):
    if request.user.has_perm('league.change_team') or \
        request.user.profile.team.pk == team_id:
        team = get_object_or_404(Team, pk=team_id)
        players = [i for i in team.team_percentile(percentile)]
        return render(request, 'teams/team.html', {'team': team, 'players': players, 
                    'subtitle': f"{team}: ({percentile}% percentile)" })
    else:
        return HttpResponse('Unauthorized', status=401)

@permission_required('league.view_team')
def team(request, pk):
    """
    view team, official and coach access only
    """
    if request.user.has_perm('league.change_team') or \
        request.user.profile.team_id == pk:
        team = get_object_or_404(Team, pk=pk)
        players = team.player_set.all()
        return render(request, 'teams/team.html', {'team': team, 'players': players, 'subtitle': team })
    else:
        return HttpResponse('Unauthorized', status=401)

@permission_required("league.view_team")
def teams(request):
    teams = Team.objects.all()
    return render(request, 'teams/index.html', {'teams': team, 'subtitle': 'Team Progress' })


@login_required
def game(request, pk):
    game = get_object_or_404(Game, pk=pk)
    team_games = game.teamgame_set.all()
    return render(request, 'games/game.html', 
                {'game': game, 
                 'team_games': team_games,
                 'subtitle': f'Scoreboard - Round {game.round}' })


@login_required
def round(request, season_pk, round):
    season = get_object_or_404(Season, pk=season_pk)
    games = Game.objects.filter(season__pk=season_pk, round=round)
    return render(request, 'teams/scoreboard.html', 
                  {'season': season, 'games':games, 
                   'subtitle': f'Scoreboard - Round {round}' })

@login_required
def scoreboard(request):
    season = get_object_or_404(Season, current_season=True)
    games = Game.objects.filter(season=season, round=season.current_round)
    return render(request, 'teams/scoreboard.html', {'season': season, 'games':games, 
                  'subtitle': 'Current Scoreboard - Round %s' % season.current_round })


@permission_required('league.view_profile')
def stats(request):
    profiles = Profile.objects.all()
    return render(request, 'site/stats.html', {'profiles': profiles, 'subtitle': 'Site Usage Stats'})

def index(request):
    return scoreboard(request)

