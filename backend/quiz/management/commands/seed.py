"""Load the demo users, football history content and sample attempts into an empty database."""

import json
import os
import random
from dataclasses import dataclass
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Profile
from quiz.models import Choice, Era, Question, Topic
from quiz.scoring import create_attempt

SEED_DATA_DIR = Path(__file__).resolve().parents[2] / "seed_data"
DEFAULT_SEED_PASSWORD = "football123"
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin12345"
CURATOR = "curator"


class Command(BaseCommand):
    help = "Load quiz/seed_data/*.json into a database that has no users and no eras yet."

    def handle(self, *args: str, **options: str) -> None:
        if User.objects.exists() or Era.objects.exists():
            self.stdout.write("Database already has data, skipping seed.")
            return
        seed_everything()
        self.stdout.write(self.style.SUCCESS(f"Seeded {Question.objects.count()} questions."))


def read_seed_file(name: str) -> list[dict]:
    return json.loads((SEED_DATA_DIR / f"{name}.json").read_text(encoding="utf-8"))


@dataclass(frozen=True)
class SeededContent:
    """Seeded rows by their JSON identifiers, so later files can reference earlier ones."""

    users: dict[str, User]
    eras: dict[str, Era]
    topics: dict[str, Topic]


@transaction.atomic
def seed_everything() -> None:
    create_admin()
    content = SeededContent(
        users={user.username: user for user in map(create_player, read_seed_file("users"))},
        eras={era.name: era for era in (Era.objects.create(**data) for data in read_seed_file("eras"))},
        topics={topic.slug: topic for topic in (Topic.objects.create(**data) for data in read_seed_file("topics"))},
    )
    questions = {data["key"]: create_question(data, content) for data in read_seed_file("questions")}
    for data in read_seed_file("attempts"):
        create_seed_attempt(data, content, questions)


def create_admin() -> User:
    return User.objects.create_superuser(
        username=os.environ.get("ADMIN_USERNAME", DEFAULT_ADMIN_USERNAME),
        password=os.environ.get("ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD),
    )


def create_player(data: dict) -> User:
    password = os.environ.get("SEED_PASSWORD", DEFAULT_SEED_PASSWORD)
    user = User.objects.create_user(data["username"], password=password, is_staff=bool(data.get("is_staff")))
    Profile.objects.filter(user=user).update(**data["profile"])
    return user


def create_question(data: dict, content: SeededContent) -> Question:
    question = Question.objects.create(
        text=data["text"],
        difficulty=data["difficulty"],
        explanation=data["explanation"],
        era=content.eras[data["era"]],
        author=content.users[data.get("author", CURATOR)],
    )
    question.topics.set(content.topics[slug] for slug in data["topics"])
    Choice.objects.bulk_create(shuffled_choices(question, data))
    return question


def shuffled_choices(question: Question, data: dict) -> list[Choice]:
    """Mix the correct answer in among the wrong ones, in the same order on every seed."""
    choices = [
        Choice(question=question, text=data["answer"], is_correct=True),
        *(Choice(question=question, text=text) for text in data["wrong"]),
    ]
    random.Random(data["key"]).shuffle(choices)
    return choices


def create_seed_attempt(data: dict, content: SeededContent, questions: dict[str, Question]) -> None:
    answers = [(questions[key], chosen_choice(questions[key], outcome)) for key, outcome in data["answers"]]
    create_attempt(
        content.users[data["user"]],
        era=content.eras.get(data.get("era")),
        topic=content.topics.get(data.get("topic")),
        answers=answers,
    )


def chosen_choice(question: Question, outcome: str) -> Choice | None:
    if outcome == "skip":
        return None
    wants_correct = outcome == "right"
    return next(choice for choice in question.choices.all() if choice.is_correct == wants_correct)
