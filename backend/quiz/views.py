from django.db.models import QuerySet
from rest_framework import serializers, viewsets
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from quiz.models import Choice, Era, Question, Topic
from quiz.permissions import IsAuthorOrStaffOrReadOnly, IsStaffOrReadOnly, is_author_or_staff
from quiz.serializers import ChoiceSerializer, EraSerializer, QuestionSerializer, TopicSerializer, choice_set_errors

NOT_YOUR_QUESTION = "Only the question's author or staff can change its choices."


class EraViewSet(viewsets.ModelViewSet):
    queryset = Era.objects.all()
    serializer_class = EraSerializer
    permission_classes = [IsStaffOrReadOnly]


class TopicViewSet(viewsets.ModelViewSet):
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    permission_classes = [IsStaffOrReadOnly]


class QuestionViewSet(viewsets.ModelViewSet):
    """Public question bank. ``?mine=true`` lists the logged-in user's own questions."""

    serializer_class = QuestionSerializer
    permission_classes = [IsAuthorOrStaffOrReadOnly]

    def get_queryset(self) -> QuerySet[Question]:
        questions = Question.objects.select_related("era", "author").prefetch_related("topics", "choices")
        if self.request.query_params.get("mine") != "true":
            return questions
        if not self.request.user.is_authenticated:
            raise NotAuthenticated
        return questions.filter(author=self.request.user)

    def perform_create(self, serializer: QuestionSerializer) -> None:
        serializer.save(author=self.request.user)


class ChoiceViewSet(viewsets.ModelViewSet):
    """Standalone choice CRUD; every write keeps the parent question at 2–4 choices with one correct."""

    queryset = Choice.objects.select_related("question")
    serializer_class = ChoiceSerializer
    permission_classes = [IsAuthorOrStaffOrReadOnly]

    def perform_create(self, serializer: ChoiceSerializer) -> None:
        self.check_question_owner(serializer.validated_data["question"])
        serializer.save()

    def perform_update(self, serializer: ChoiceSerializer) -> None:
        self.check_question_owner(serializer.validated_data.get("question", serializer.instance.question))
        serializer.save()

    def perform_destroy(self, choice: Choice) -> None:
        remaining = choice.question.choices.exclude(pk=choice.pk).values_list("is_correct", flat=True)
        errors = choice_set_errors(list(remaining))
        if errors:
            raise serializers.ValidationError({"question": errors})
        choice.delete()

    def check_question_owner(self, question: Question) -> None:
        if not is_author_or_staff(self.request.user, question):
            raise PermissionDenied(NOT_YOUR_QUESTION)
