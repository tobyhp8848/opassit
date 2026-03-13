# Generated manually - add task_id field

import random
import string

from django.db import migrations, models


def generate_task_id():
    """生成 TASK + 6 位字母数字，共 10 位"""
    chars = string.ascii_uppercase + string.digits
    return "TASK" + "".join(random.choices(chars, k=6))


def backfill_task_ids(apps, schema_editor):
    AutomationTask = apps.get_model("automation", "AutomationTask")
    used = set(AutomationTask.objects.exclude(task_id__isnull=True).exclude(task_id="").values_list("task_id", flat=True))
    for task in AutomationTask.objects.filter(task_id__isnull=True) | AutomationTask.objects.filter(task_id=""):
        while True:
            tid = generate_task_id()
            if tid not in used:
                used.add(tid)
                task.task_id = tid
                task.save(update_fields=["task_id"])
                break


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("automation", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="automationtask",
            name="task_id",
            field=models.CharField(
                blank=True,
                max_length=10,
                null=True,
                unique=True,
                verbose_name="任务ID",
            ),
        ),
        migrations.RunPython(backfill_task_ids, noop),
        migrations.AlterField(
            model_name="automationtask",
            name="task_id",
            field=models.CharField(
                max_length=10,
                unique=True,
                verbose_name="任务ID",
            ),
        ),
    ]
