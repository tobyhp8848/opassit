# Generated manually - 为已有任务生成 task_id
from django.db import migrations
from django.db.models import Q


def generate_task_id():
    """生成 TASK + 6位英数 的唯一ID"""
    import random
    import string

    chars = string.ascii_uppercase + string.digits
    return "TASK" + "".join(random.choices(chars, k=6))


def backfill_task_ids(apps, schema_editor):
    AutomationTask = apps.get_model("automation", "AutomationTask")
    exists = set()
    for task in AutomationTask.objects.filter(task_id__isnull=True) | AutomationTask.objects.filter(
        task_id=""
    ):
        while True:
            tid = generate_task_id()
            if tid not in exists and not AutomationTask.objects.filter(task_id=tid).exists():
                break
        exists.add(tid)
        task.task_id = tid
        task.save()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("automation", "0002_automationtask_task_id"),
    ]

    operations = [
        migrations.RunPython(backfill_task_ids, noop),
    ]
