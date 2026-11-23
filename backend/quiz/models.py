"""Football history content (eras, topics, questions, choices) and quiz attempts."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

PERCENT = 100


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Era(TimestampedModel):
    name = models.CharField(max_length=100, unique=True)
    start_year = models.PositiveSmallIntegerField()
    end_year = models.PositiveSmallIntegerField()
    summary = models.TextField(blank=True)

    class Meta:
        ordering = ["start_year"]

    def __str__(self) -> str:
        return f"{self.name} ({self.start_year}–{self.end_year})"

    def clean(self) -> None:
        if self.start_year > self.end_year:
            raise ValidationError({"end_year": "The era cannot end before it starts."})


class Topic(TimestampedModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Difficulty(models.TextChoices):
    EASY = "easy", "Easy"
    MEDIUM = "medium", "Medium"
    HARD = "hard", "Hard"


class Question(TimestampedModel):
    text = models.TextField()
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM)
    explanation = models.TextField(blank=True)
    era = models.ForeignKey(Era, on_delete=models.CASCADE, related_name="questions")
    topics = models.ManyToManyField(Topic, related_name="questions", blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="questions")

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.text


class Choice(TimestampedModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.text


class QuizAttempt(TimestampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attempts")
    era = models.ForeignKey(Era, on_delete=models.SET_NULL, null=True, blank=True, related_name="attempts")
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True, related_name="attempts")
    score = models.PositiveSmallIntegerField(default=0)
    total = models.PositiveSmallIntegerField(default=0)
    questions = models.ManyToManyField(Question, through="AttemptAnswer", related_name="attempts")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user} {self.score}/{self.total}"

    @property
    def percent(self) -> int:
        if self.total == 0:
            return 0
        return round(PERCENT * self.score / self.total)


class AttemptAnswer(TimestampedModel):
    """One answered question of an attempt, with a text snapshot that survives edits and deletes."""

    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.SET_NULL, null=True, related_name="attempt_answers")
    choice = models.ForeignKey(Choice, on_delete=models.SET_NULL, null=True, blank=True, related_name="attempt_answers")
    is_correct = models.BooleanField(default=False)
    question_text = models.TextField()
    chosen_text = models.CharField(max_length=200, blank=True)
    correct_text = models.CharField(max_length=200)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(fields=["attempt", "question"], name="unique_answer_per_attempt_question"),
        ]

    def __str__(self) -> str:
        return f"{self.attempt_id}: {self.question_text}"
