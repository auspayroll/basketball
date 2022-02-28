import random
from functools import reduce
from django.db import models
from django.db.models.fields import IntegerField
from django.db.models.fields.related import ForeignKey
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import User, Group, Permission
from django.db.models.signals import post_save
from django.db.models import F
from django.dispatch import receiver


class Team(models.Model):
    name = models.CharField(max_length=200)
    total_games = models.IntegerField(default=0)
    total_score = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    def team_percentile(self, percentile):
        player_list = [player for player in self.player_set.order_by(F('total_score') / F('total_games'))]
        total = len(player_list)
        for i, player in enumerate(player_list):
            if i/total * 100 <= percentile:
                yield player
            else:
                break

    @property
    def average_score(self):
        try:
            return round(self.total_score/self.total_games, 2)
        except ZeroDivisionError:
            return 0


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    team = models.OneToOneField(Team, null=True, on_delete=models.CASCADE)
    last_logout = models.DateTimeField(null=True)
    total_seconds = models.IntegerField(default=0)
    login_count = models.IntegerField(default=0)
    
    @property
    def status(self):
        if not self.user.last_login:
            return 0, "hasn't logged in yet"
        elif self.user.last_login and not self.last_logout:
            return 1, "first time logged in now"
        elif self.last_logout < self.user.last_login:
            return 2, "logged in now"
        return 3, "logged out"

    def __str__(self):
        return ((self.user.first_name or '') + \
               (self.user.last_name or '')) \
                or self.user.email

    @property
    def total_time(self):
        hours, seconds = divmod(self.total_seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return "%s-hrs %s-mins %s-secs" % (hours, minutes, seconds)


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        try:
            Profile.objects.get(user=instance)
        except Profile.DoesNotExist:
            Profile.objects.create(user=instance)


class Season(models.Model):
    year = models.IntegerField()
    current_round = models.IntegerField(default=1)
    current_season = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.year} season"

    def next_round(self):
        pass


class Player(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    height = models.FloatField(
        validators= [
            MaxValueValidator(300),
            MinValueValidator(100)
        ],
        verbose_name="height (cm)")

    total_games = models.IntegerField(default=0)
    total_score = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    @property
    def average_score(self):
        try:
            return round(self.total_score/self.total_games, 2)
        except ZeroDivisionError:
            return 0


class Game(models.Model):
    number = models.IntegerField()
    season = models.ForeignKey(Season, null=True, on_delete=models.SET_NULL)
    winner = models.ForeignKey(Team, null=True, on_delete=models.SET_NULL)
    when = models.DateField(null=True)
    round = models.IntegerField(null=True)

    def __str__(self):
        return " -vs- ".join([team_game.team.name for team_game in self.teamgame_set.all()])

    # @property
    def score(self):
        return " - ".join([str(team.score) for team in self.teams])

    @property
    def teams(self):
        return self.teamgame_set.all().order_by('-score')

    def calc_scores(self):
        team_games = self.teamgame_set.all()
        for team_game in team_games:
            team_game.calc_scores()
        def highest(x,y):
            if x.score > y.score:
                return x.team
            else:
                return y.team
        self.winner = reduce(highest, team_games)
        self.save()


class TeamGame(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.team.name} - {self.game}"

    def calc_scores(self):
        players = self.playergame_set.all()
        self.score = players.aggregate(models.Sum('score'))['score__sum']
        self.save()
        self.team.total_score += self.score
        self.team.total_games += 1
        self.team.save()

 
class PlayerGame(models.Model):
    team_game = models.ForeignKey(TeamGame, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.player.total_score += self.score
        self.player.total_games += 1
        self.player.save()
