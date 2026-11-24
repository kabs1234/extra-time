"""Turn a player's submitted answers into a saved, scored attempt."""

from collections.abc import Sequence

from django.contrib.auth.models import User
from django.db import transaction

from quiz.models import AttemptAnswer, Choice, Era, Question, QuizAttempt, Topic

AnsweredQuestion = tuple[Question, Choice | None]


@transaction.atomic
def create_attempt(
    user: User, *, era: Era | None, topic: Topic | None, answers: Sequence[AnsweredQuestion]
) -> QuizAttempt:
    attempt = QuizAttempt.objects.create(user=user, era=era, topic=topic, total=len(answers))
    rows = AttemptAnswer.objects.bulk_create(
        snapshot_answer(attempt, question, choice) for question, choice in answers
    )
    attempt.score = sum(row.is_correct for row in rows)
    attempt.save(update_fields=["score"])
    return attempt


def snapshot_answer(attempt: QuizAttempt, question: Question, choice: Choice | None) -> AttemptAnswer:
    """Copy the texts now, so later edits or deletes of the question never rewrite this answer."""
    correct = next((candidate for candidate in question.choices.all() if candidate.is_correct), None)
    return AttemptAnswer(
        attempt=attempt,
        question=question,
        choice=choice,
        is_correct=choice is not None and correct is not None and choice.pk == correct.pk,
        question_text=question.text,
        chosen_text=choice.text if choice else "",
        correct_text=correct.text if correct else "",
        explanation=question.explanation,
    )
