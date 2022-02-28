from django.test import TestCase
from league.models import *
from league.utils import *
from django.test import Client
from django.test.utils import setup_test_environment
from django.urls import reverse
import time


players_per_team = 10
total_teams = 16

def load_test_data():
    add_users_groups()
    add_teams_players()


class LeagueTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        add_users_groups()
        add_teams_players()
        create_new_draw()
        add_dummy_results()
        close_round()

    def test_season_insert(self):
        season = Season.objects.get(year=2022)
        self.assertEqual(season.current_round, 1)
        self.assert_(season.current_season)

    def test_team_insert(self):
        self.assertEqual(Team.objects.all().count(), 16)

    def test_player_insert(self):
        self.assertEqual(Player.objects.all().count(), players_per_team * total_teams)
        random_team = Team.objects.order_by("?").first()
        self.assertEqual(random_team.player_set.all().count(), players_per_team)

    def test_created_games(self):
        self.assertEqual(Game.objects.all().count(), total_teams/2)
        self.assertEqual(Game.objects.filter(winner__isnull=False).count(), total_teams/2)
        self.assertEqual(TeamGame.objects.all().count(), total_teams)
        self.assertEqual(Team.objects.filter(total_games=1).count(), total_teams)
        for game in Game.objects.all(): # 2 teams per game
            self.assertEqual(game.teamgame_set.all().count(), 2)

    def test_totals(self):
        for team in Team.objects.all():
            player_total = team.player_set.aggregate(models.Sum('total_score'))['total_score__sum']
            self.assertEqual(team.total_score, player_total)

    def test_averages_round_1(self):
        for team in Team.objects.all():
            self.assertEqual(team.average_score, team.total_score)

    def test_user_coach(self):
        coach = User.objects.filter(groups__name='Coach').first()
        self.assert_(isinstance(coach.profile, Profile))
        self.assert_(coach.has_perm('league.view_player'))
        self.assert_(coach.has_perm('league.view_team'))

    def test_user_official(self):
        official = User.objects.filter(groups__name='Official').first()
        self.assert_(isinstance(official.profile, Profile))
        self.assert_(official.has_perm('league.view_player'))
        self.assert_(official.has_perm('league.view_team'))
        self.assert_(official.has_perm('league.change_player'))
        self.assert_(official.has_perm('league.change_team'))

    def test_user_player(self):
        player = User.objects.filter(groups__name='Player').first()
        self.assert_(isinstance(player.profile, Profile))
        self.assertEqual(player.user_permissions.count(),0)

    def test_percentile(self):
        team = Team.objects.first()
        percentiles = [90,80,70,60,50,40,30]
        expected_lengths = [10,9,8,7,6,5,4]
        for percentile, expected_length in tuple(zip(percentiles, expected_lengths)):
            players = list(team.team_percentile(percentile))
            self.assertEqual(len(players), expected_length)

    def test_logins(self):
        client = Client()
        username = 'player'
        user = User.objects.get(username=username)
        self.assertEqual(user.profile.login_count, 0)
        self.assertEqual(user.profile.total_seconds, 0)
        self.assertEqual(user.profile.last_logout, None)
        #invalid login
        response = client.post(reverse('league_login'), {'username': username, 'password': "wrong password"})
        self.assertNotEqual(response.status_code, 302)
        # valid login and redirect
        response = client.post(reverse('league_login'), {'username': 'player', 'password': demo_password})

        user.refresh_from_db()
        user.profile.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('scoreboard'))
        self.assertEqual(user.profile.login_count, 1)
        self.assertEqual(user.profile.total_seconds, 0)
        self.assertEqual(user.profile.last_logout, None)
        time.sleep(2)
        # logout
        response = client.post(reverse('league_logout'))
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        user.profile.refresh_from_db()
        self.assertNotEqual(user.profile.last_logout, None)
        self.assertNotEqual(user.profile.total_seconds, 0)

