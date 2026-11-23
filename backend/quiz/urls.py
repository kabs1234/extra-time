from rest_framework.routers import DefaultRouter

from quiz import views

router = DefaultRouter()
router.register("eras", views.EraViewSet, basename="era")
router.register("topics", views.TopicViewSet, basename="topic")
router.register("questions", views.QuestionViewSet, basename="question")
router.register("choices", views.ChoiceViewSet, basename="choice")

urlpatterns = router.urls
