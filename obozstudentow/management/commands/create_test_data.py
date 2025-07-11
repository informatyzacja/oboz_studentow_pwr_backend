from django.core.management.base import BaseCommand

from obozstudentow.models import *
from datetime import date
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = "Fill database with test data"

    # def add_arguments(self, parser):
    #     # Dodaj opcjonalne argumenty, jeśli potrzebne
    #     parser.add_argument('parametr', type=str, help='Opis parametru')

    def handle(self, *args, **kwargs):
        Workshop.objects.create(
            name="Warsztat 1",
            description="Opis warsztatu 1",
            start=datetime.now() + timedelta(hours=1),
            end=datetime.now() + timedelta(hours=2),
            location="Sala 1",
            userLimit=10,
            signupsOpen=True,
        )

        self.stdout.write(self.style.SUCCESS("Successfully created test data"))
