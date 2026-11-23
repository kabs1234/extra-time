from django.urls import path
from rest_framework.routers import DefaultRouter

from quiz import views

router = DefaultRouter()
router.register("eras", views.EraViewSet, basename="era")
router.register("topics", views.TopicViewSet, basename="topic")
router.register("questions", views.QuestionViewSet, basename="question")
router.register("choices", views.ChoiceViewSet, basename="choice")
router.register("attempts", views.AttemptViewSet, basename="attempt")

urlpatterns = [
    path("quiz/", views.QuizView.as_view(), name="quiz"),
    path("leaderboard/", views.LeaderboardView.as_view(), name="leaderboard"),
    *router.urls,
]
