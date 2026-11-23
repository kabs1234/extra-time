from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Load the demo data if the database is empty (filled in once the models exist)."

    def handle(self, *args: str, **options: str) -> None:
        self.stdout.write("Nothing to seed yet.")
