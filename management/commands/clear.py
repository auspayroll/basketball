from django.core.management.base import BaseCommand, CommandError
from league.models import *


class Command(BaseCommand):
    help = 'Clears League database'


    def handle(self, *args, **options):
        PlayerGame.objects.all().delete()
        TeamGame.objects.all().delete()
        Player.objects.all().delete()
        Team.objects.all().delete()
        Game.objects.all().delete()
        Season.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Successfully deleted test data'))