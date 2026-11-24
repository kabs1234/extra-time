from django.apps.registry import Apps
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def copy_explanations_from_questions(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """Rounds played before this migration take the explanation their question has now."""
    attempt_answer = apps.get_model("quiz", "AttemptAnswer")
    for answer in attempt_answer.objects.filter(question__isnull=False).select_related("question"):
        answer.explanation = answer.question.explanation
        answer.save(update_fields=["explanation"])


class Migration(migrations.Migration):

    dependencies = [
        ("quiz", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="attemptanswer",
            name="explanation",
            field=models.TextField(blank=True),
        ),
        migrations.RunPython(copy_explanations_from_questions, migrations.RunPython.noop),
    ]
