from django.core.management.base import BaseCommand, CommandError
from league.utils import *

class Command(BaseCommand):
    help = 'Loads initial data'

    def handle(self, *args, **options):
        simulate_season()
        self.stdout.write(self.style.SUCCESS('Successfully created test data'))