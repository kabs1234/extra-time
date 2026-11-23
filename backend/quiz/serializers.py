from collections.abc import Sequence

from django.db import transaction
from rest_framework import serializers

from quiz.models import Choice, Era, Question, Topic
from quiz.permissions import can_see_answers

MIN_CHOICES = 2
MAX_CHOICES = 4
ANSWER_FIELDS = ("is_correct",)


def choice_set_errors(correct_flags: Sequence[bool]) -> list[str]:
    """Rules every question's choice set obeys: 2–4 choices, exactly one of them correct."""
    errors = []
    if not MIN_CHOICES <= len(correct_flags) <= MAX_CHOICES:
        errors.append(f"A question needs {MIN_CHOICES} to {MAX_CHOICES} choices.")
    if sum(correct_flags) != 1:
        errors.append("Exactly one choice must be marked correct.")
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
        errors = choice_set_errors([bool(choice.get("is_correct")) for choice in choices])
        if errors:
            raise serializers.ValidationError(errors)
        return choices

    def to_representation(self, question: Question) -> dict:
        data = super().to_representation(question)
        if can_see_answers(self.context["request"].user, question):
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
        question = attrs.get("question", getattr(self.instance, "question", None))
        is_correct = attrs["is_correct"] if "is_correct" in attrs else bool(self.instance and self.instance.is_correct)
        siblings = question.choices.exclude(pk=getattr(self.instance, "pk", None))
        errors = choice_set_errors([*siblings.values_list("is_correct", flat=True), is_correct])
        if errors:
            raise serializers.ValidationError({"question": errors})
        return attrs

    def to_representation(self, choice: Choice) -> dict:
        data = super().to_representation(choice)
        if can_see_answers(self.context["request"].user, choice.question):
            return data
        return without_answer(data)
