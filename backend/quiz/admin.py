from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet

from quiz.models import AttemptAnswer, Choice, Era, Question, QuizAttempt, Topic
from quiz.serializers import choice_set_errors


class ChoiceInlineFormSet(BaseInlineFormSet):
    """The admin keeps the same rule as the API: 2-4 choices, exactly one correct."""

    def clean(self) -> None:
        super().clean()
        kept_forms = [form for form in self.forms if form.cleaned_data and not form.cleaned_data.get("DELETE")]
        errors = choice_set_errors([bool(form.cleaned_data.get("is_correct")) for form in kept_forms])
        if errors:
            raise ValidationError(errors)


class ChoiceInline(admin.TabularInline):
    model = Choice
    formset = ChoiceInlineFormSet
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
