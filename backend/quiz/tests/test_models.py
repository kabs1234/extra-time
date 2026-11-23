from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from quiz.models import AttemptAnswer, Choice, Era, Question, QuizAttempt


class EraTests(TestCase):
    def test_era_rejects_start_after_end(self) -> None:
        era = Era(name="Backwards", start_year=1950, end_year=1900, summary="")

        with self.assertRaises(ValidationError):
            era.full_clean()


class AttemptTests(TestCase):
    def setUp(self) -> None:
        self.player = User.objects.create_user("player", password="pw-for-tests-1")
        self.era = Era.objects.create(name="Origins", start_year=1863, end_year=1900, summary="")
        self.question = Question.objects.create(
            text="When was the FA founded?",
            explanation="The Football Association was formed in London in 1863.",
            era=self.era,
            author=self.player,
        )
        self.correct = Choice.objects.create(question=self.question, text="1863", is_correct=True)

    def test_deleting_question_keeps_attempt_answer(self) -> None:
        attempt = QuizAttempt.objects.create(user=self.player, score=1, total=1)
        answer = AttemptAnswer.objects.create(
            attempt=attempt,
            question=self.question,
            choice=self.correct,
            is_correct=True,
            question_text=self.question.text,
            chosen_text=self.correct.text,
            correct_text=self.correct.text,
        )

        self.question.delete()

        answer.refresh_from_db()
        attempt.refresh_from_db()
        self.assertIsNone(answer.question)
        self.assertIsNone(answer.choice)
        self.assertEqual(answer.question_text, "When was the FA founded?")
        self.assertEqual(attempt.score, 1)

    def test_attempt_percent(self) -> None:
        self.assertEqual(QuizAttempt(user=self.player, score=7, total=10).percent, 70)
        self.assertEqual(QuizAttempt(user=self.player, score=0, total=0).percent, 0)
