from django.contrib.auth.models import User
from django.core.management import call_command
from django.db.models import Count, F, Q
from django.test import TestCase

from accounts.models import Profile
from quiz.models import AttemptAnswer, Choice, Era, Question, QuizAttempt, Topic

MIN_ROWS = 10
MIN_QUESTIONS = 40


class SeedTests(TestCase):
    def test_seed_fills_every_table_with_ten_rows(self) -> None:
        call_command("seed", verbosity=0)

        for model in (User, Profile, Era, Topic, Question, Choice, QuizAttempt, AttemptAnswer):
            with self.subTest(model=model.__name__):
                self.assertGreaterEqual(model.objects.count(), MIN_ROWS)
        self.assertGreaterEqual(Question.objects.count(), MIN_QUESTIONS)
        correct_counts = Question.objects.annotate(correct=Count("choices", filter=Q(choices__is_correct=True)))
        self.assertFalse(correct_counts.exclude(correct=1).exists())

    def test_seed_twice_does_not_duplicate(self) -> None:
        call_command("seed", verbosity=0)
        counts = (User.objects.count(), Question.objects.count(), QuizAttempt.objects.count())

        call_command("seed", verbosity=0)

        self.assertEqual((User.objects.count(), Question.objects.count(), QuizAttempt.objects.count()), counts)

    def test_seed_creates_admin_and_players_with_questions(self) -> None:
        call_command("seed", verbosity=0)

        self.assertTrue(User.objects.get(username="admin").is_superuser)
        self.assertTrue(User.objects.get(username="curator").is_staff)
        self.assertGreaterEqual(Question.objects.filter(author__is_staff=False).count(), 5)
        self.assertFalse(AttemptAnswer.objects.filter(question__author=F("attempt__user")).exists())
