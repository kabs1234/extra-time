from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework import generics, mixins, serializers, status, viewsets
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from quiz.leaderboard import leaderboard_rows
from quiz.models import Choice, Era, Question, QuizAttempt, Topic
from quiz.permissions import IsAuthorOrStaffOrReadOnly, IsStaffOrReadOnly, is_author_or_staff
from quiz.serializers import (
    AttemptCreateSerializer,
    AttemptSerializer,
    ChoiceSerializer,
    EraSerializer,
    LeaderboardRowSerializer,
    QuestionSerializer,
    QuizParamsSerializer,
    QuizQuestionSerializer,
    TopicSerializer,
    choice_set_errors,
)

NOT_YOUR_QUESTION = "Only the question's author or staff can change its choices."
MIN_QUIZ_LENGTH = 5
MAX_QUIZ_LENGTH = 20


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


class QuizView(generics.GenericAPIView):
    """Random questions to play, never the player's own. ``count`` is clamped to 5–20."""

    serializer_class = QuizQuestionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    @extend_schema(parameters=[QuizParamsSerializer], responses={200: QuizQuestionSerializer(many=True)})
    def get(self, request: Request) -> Response:
        params = QuizParamsSerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        questions = self.pick_questions(**params.validated_data)
        return Response(self.get_serializer(questions, many=True).data)

    def pick_questions(self, *, count: int, era: Era | None = None, topic: Topic | None = None) -> list[Question]:
        questions = Question.objects.exclude(author=self.request.user).prefetch_related("topics", "choices")
        if era is not None:
            questions = questions.filter(era=era)
        if topic is not None:
            questions = questions.filter(topics=topic)
        quiz_length = min(max(count, MIN_QUIZ_LENGTH), MAX_QUIZ_LENGTH)
        return list(questions.select_related("era", "author").order_by("?")[:quiz_length])


class AttemptViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """A player's own attempts (staff see all). Attempts are a record, so they cannot be edited."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[QuizAttempt]:
        attempts = QuizAttempt.objects.select_related("era", "topic").prefetch_related("answers__question")
        if self.request.user.is_staff:
            return attempts
        return attempts.filter(user=self.request.user)

    def get_serializer_class(self) -> type[serializers.Serializer]:
        if self.action == "create":
            return AttemptCreateSerializer
        return AttemptSerializer

    @extend_schema(request=AttemptCreateSerializer, responses={201: AttemptSerializer})
    def create(self, request: Request) -> Response:
        submission = self.get_serializer(data=request.data)
        submission.is_valid(raise_exception=True)
        attempt = submission.save()
        return Response(AttemptSerializer(self.get_queryset().get(pk=attempt.pk)).data, status=status.HTTP_201_CREATED)


class LeaderboardView(generics.GenericAPIView):
    serializer_class = LeaderboardRowSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    @extend_schema(responses={200: LeaderboardRowSerializer(many=True)})
    def get(self, request: Request) -> Response:
        return Response(leaderboard_rows())
