from collections.abc import Sequence

from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from quiz.models import AttemptAnswer, Choice, Era, Question, QuizAttempt, Topic
from quiz.permissions import can_see_answers, is_author_or_staff
from quiz.scoring import create_attempt

MIN_CHOICES = 2
MAX_CHOICES = 4
ANSWER_FIELDS = ("is_correct",)
NOT_YOUR_QUESTION = "Only the question's author or staff can change its choices."


def choice_set_errors(choices: Sequence[tuple[str, bool]]) -> list[str]:
    """
    Rules every question's choice set obeys, given as ``(text, is_correct)`` pairs: 2–4 choices,
    exactly one of them correct, and no two with the same text (ignoring case and outer spaces).
    """
    errors = []
    if not MIN_CHOICES <= len(choices) <= MAX_CHOICES:
        errors.append(f"A question needs {MIN_CHOICES} to {MAX_CHOICES} choices.")
    if sum(is_correct for _, is_correct in choices) != 1:
        errors.append("Exactly one choice must be marked correct.")
    texts = [text.strip().casefold() for text, _ in choices]
    if len(set(texts)) != len(texts):
        errors.append("Two choices can't have the same text.")
    return errors


def without_answer(choice_data: dict) -> dict:
    return {field: value for field, value in choice_data.items() if field not in ANSWER_FIELDS}


class EraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Era
        fields = ["id", "name", "start_year", "end_year", "summary", "created_at", "updated_at"]

    def validate(self, attrs: dict) -> dict:
        start_year = attrs.get("start_year", getattr(self.instance, "start_year", None))
        end_year = attrs.get("end_year", getattr(self.instance, "end_year", None))
        if start_year is not None and end_year is not None and start_year > end_year:
            raise serializers.ValidationError({"end_year": "The era cannot end before it starts."})
        return attrs


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ["id", "name", "slug", "description", "created_at", "updated_at"]


class NestedChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "text", "is_correct"]


class QuestionSerializer(serializers.ModelSerializer):
    """A question with its choices. Answers (``is_correct``, ``explanation``) only reach the author and staff."""

    era_name = serializers.CharField(source="era.name", read_only=True)
    topic_names = serializers.SlugRelatedField(source="topics", slug_field="name", many=True, read_only=True)
    author = serializers.CharField(source="author.username", read_only=True)
    choices = NestedChoiceSerializer(many=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "text",
            "difficulty",
            "explanation",
            "era",
            "era_name",
            "topics",
            "topic_names",
            "author",
            "choices",
            "created_at",
            "updated_at",
        ]

    def validate_choices(self, choices: list[dict]) -> list[dict]:
        errors = choice_set_errors([(choice["text"], bool(choice.get("is_correct"))) for choice in choices])
        if errors:
            raise serializers.ValidationError(errors)
        return choices

    def shows_answers(self, question: Question) -> bool:
        return can_see_answers(self.context["request"].user, question)

    def to_representation(self, question: Question) -> dict:
        data = super().to_representation(question)
        if self.shows_answers(question):
            return data
        hidden = {field: value for field, value in data.items() if field != "explanation"}
        hidden["choices"] = [without_answer(choice) for choice in data["choices"]]
        return hidden

    @transaction.atomic
    def create(self, validated_data: dict) -> Question:
        choices = validated_data.pop("choices")
        topics = validated_data.pop("topics", [])
        question = Question.objects.create(**validated_data)
        question.topics.set(topics)
        replace_choices(question, choices)
        return question

    @transaction.atomic
    def update(self, question: Question, validated_data: dict) -> Question:
        choices = validated_data.pop("choices", None)
        topics = validated_data.pop("topics", None)
        question = super().update(question, validated_data)
        if topics is not None:
            question.topics.set(topics)
        if choices is not None:
            replace_choices(question, choices)
        return question


def replace_choices(question: Question, choices: list[dict]) -> None:
    question.choices.all().delete()
    Choice.objects.bulk_create(Choice(question=question, **choice) for choice in choices)


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "question", "text", "is_correct", "created_at", "updated_at"]

    def validate(self, attrs: dict) -> dict:
        if self.instance is not None and attrs.get("question", self.instance.question) != self.instance.question:
            raise serializers.ValidationError({"question": "A choice can't move to another question."})
        question = attrs.get("question", getattr(self.instance, "question", None))
        if not is_author_or_staff(self.context["request"].user, question):
            raise PermissionDenied(NOT_YOUR_QUESTION)
        is_correct = attrs["is_correct"] if "is_correct" in attrs else bool(self.instance and self.instance.is_correct)
        text = attrs.get("text", getattr(self.instance, "text", ""))
        siblings = question.choices.exclude(pk=getattr(self.instance, "pk", None))
        errors = choice_set_errors([*siblings.values_list("text", "is_correct"), (text, is_correct)])
        if errors:
            raise serializers.ValidationError({"question": errors})
        return attrs

    def to_representation(self, choice: Choice) -> dict:
        data = super().to_representation(choice)
        if can_see_answers(self.context["request"].user, choice.question):
            return data
        return without_answer(data)


class QuizQuestionSerializer(QuestionSerializer):
    """A question served for play: never carries the answer, even to staff."""

    def shows_answers(self, question: Question) -> bool:
        return False


class QuizParamsSerializer(serializers.Serializer):
    era = serializers.PrimaryKeyRelatedField(queryset=Era.objects.all(), required=False)
    topic = serializers.PrimaryKeyRelatedField(queryset=Topic.objects.all(), required=False)
    count = serializers.IntegerField(required=False, default=10)


class AnswerInputSerializer(serializers.Serializer):
    """One answer. A choice id that no longer exists (the author edited the question mid-round) counts as skipped."""

    question = serializers.PrimaryKeyRelatedField(queryset=Question.objects.prefetch_related("choices"))
    choice = serializers.IntegerField(allow_null=True)

    def validate(self, attrs: dict) -> dict:
        choice = Choice.objects.filter(pk=attrs["choice"]).first() if attrs["choice"] is not None else None
        if choice is not None and choice.question_id != attrs["question"].id:
            raise serializers.ValidationError({"choice": "This choice belongs to a different question."})
        return {**attrs, "choice": choice}


class AttemptCreateSerializer(serializers.Serializer):
    era = serializers.PrimaryKeyRelatedField(queryset=Era.objects.all(), required=False, allow_null=True)
    topic = serializers.PrimaryKeyRelatedField(queryset=Topic.objects.all(), required=False, allow_null=True)
    answers = AnswerInputSerializer(many=True, allow_empty=False)

    def validate_answers(self, answers: list[dict]) -> list[dict]:
        question_ids = [answer["question"].id for answer in answers]
        if len(set(question_ids)) != len(question_ids):
            raise serializers.ValidationError("Each question can be answered only once.")
        player = self.context["request"].user
        if any(answer["question"].author_id == player.id for answer in answers):
            raise serializers.ValidationError("You cannot score points on your own questions.")
        return answers

    def create(self, validated_data: dict) -> QuizAttempt:
        return create_attempt(
            self.context["request"].user,
            era=validated_data.get("era"),
            topic=validated_data.get("topic"),
            answers=[(answer["question"], answer["choice"]) for answer in validated_data["answers"]],
        )


class AttemptAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttemptAnswer
        fields = ["question", "question_text", "chosen_text", "correct_text", "is_correct", "explanation"]


class AttemptSerializer(serializers.ModelSerializer):
    era_name = serializers.CharField(source="era.name", read_only=True, allow_null=True)
    topic_name = serializers.CharField(source="topic.name", read_only=True, allow_null=True)
    percent = serializers.IntegerField(read_only=True)
    answers = AttemptAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = QuizAttempt
        fields = ["id", "era_name", "topic_name", "score", "total", "percent", "created_at", "answers"]


class LeaderboardRowSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    username = serializers.CharField()
    favorite_club = serializers.CharField()
    attempts = serializers.IntegerField()
    total_correct = serializers.IntegerField()
    best_score_pct = serializers.IntegerField()
