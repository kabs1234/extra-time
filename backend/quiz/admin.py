from django.contrib import admin

from quiz.models import AttemptAnswer, Choice, Era, Question, QuizAttempt, Topic


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 0


class AttemptAnswerInline(admin.TabularInline):
    model = AttemptAnswer
    extra = 0


@admin.register(Era)
class EraAdmin(admin.ModelAdmin):
    list_display = ["name", "start_year", "end_year"]


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["text", "era", "difficulty", "author"]
    list_filter = ["era", "difficulty", "topics"]
    inlines = [ChoiceInline]


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ["text", "question", "is_correct"]


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ["user", "score", "total", "era", "topic", "created_at"]
    inlines = [AttemptAnswerInline]


@admin.register(AttemptAnswer)
class AttemptAnswerAdmin(admin.ModelAdmin):
    list_display = ["attempt", "question_text", "is_correct"]
