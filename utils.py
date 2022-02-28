from league.models import *

players_per_game = 5
players_per_team = 10
total_teams = 16
demo_password = "demo"

def create_draw(season, teams):
    random.shuffle(teams)
    for i, j in [(i,i+1) for i in range(len(teams))[:-1:2]]:
        game, _  = Game.objects.get_or_create(number=i, season=season, 
                                              round=season.current_round)
        team1_game = TeamGame.objects.create(game=game, team=teams[i])
        team2_game = TeamGame.objects.create(game=game, team=teams[j])
        # allocate players for each team
        team1_players = Player.objects.filter(team=teams[i])\
            .order_by("?")[:players_per_game]
        for p in team1_players:
            PlayerGame.objects.create(player=p, team_game=team1_game)
        team2_players = Player.objects.filter(team=teams[j])\
            .order_by("?")[:players_per_game]
        for p in team2_players:
            PlayerGame.objects.create(player=p, team_game=team2_game)

def create_new_draw():
    season = Season.objects.get(current_season=True)
    teams = list(Team.objects.all())
    create_draw(season, teams)


def advance_round():
    season = Season.objects.get(current_season=True)
    winners = [game.winner for game in \
               Game.objects.filter(season=season, 
               round=season.current_round)]
    if len(winners) > 1:
        season.current_round = season.current_round + 1
        season.save()
        create_draw(season, winners)
        return True
    else:
        return False


def close_round():
    season = Season.objects.get(current_season=True)
    games = Game.objects.filter(season=season,
                                round=season.current_round)
    
    for game in games:
        game.calc_scores()


def add_dummy_results():
    season = Season.objects.get(current_season=True)
    round = season.current_round
    games = Game.objects.filter(season=season, round=round)
    player_games = PlayerGame.objects.filter(team_game__game__in=games)
    for player_game in player_games:
        player_game.score = random.randint(50,100)
        player_game.save()


def clear_data():
        PlayerGame.objects.all().delete()
        TeamGame.objects.all().delete()
        Player.objects.all().delete()
        Team.objects.all().delete()
        Game.objects.all().delete()
        Season.objects.all().delete()
        Group.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()


def simulate_next_round():
    add_dummy_results()
    close_round()
    return advance_round()


def add_users_groups():
    coach = User.objects.create(username="coach", first_name="Coach", 
                        last_name="KillJoy")
    official = User.objects.create(username="official", first_name="Mr", 
                        last_name="Black")
    player = User.objects.create(username="player", first_name="Michael", 
                        last_name="Jordan")
    coach.set_password(demo_password)
    coach.save()
    official.set_password(demo_password)
    official.save()
    player.set_password(demo_password)
    player.save()
    coach_group = Group.objects.create(name="Coach")
    official_group = Group.objects.create(name="Official")
    player_group = Group.objects.create(name="Player")
    coach.groups.add(coach_group)
    official.groups.add(official_group)
    player.groups.add(player_group)
    view_team = Permission.objects.get(name='Can view team')
    edit_team = Permission.objects.get(name='Can change team')
    view_player = Permission.objects.get(name='Can view player')
    edit_player = Permission.objects.get(name='Can change player')
    view_profile = Permission.objects.get(name='Can view profile')
    official_group.permissions.add(view_team, edit_team, 
                                   view_player, edit_player, view_profile)
    coach_group.permissions.add(view_team, view_player)


def add_teams_players():
    season, _ = Season.objects.get_or_create(year=2022)
    for i in range(total_teams):
        team, _ = Team.objects.get_or_create(name=f"Team {i+1}")
        if i == 1: # allocate a coach
            coach = Profile.objects.get(user__username='coach')
            coach.team = team
            coach.save()
        for j in range(players_per_team):
            Player.objects.get_or_create(name=f"Player {(j+1) * (i+1)}", 
                                    team=team, 
                                    defaults=dict(height=random.randint(100,300)))


def simulate_season():
    clear_data()
    add_users_groups()
    add_teams_players()
    create_new_draw()
    while simulate_next_round(): 
        pass
    add_dummy_results()  # pick the winner