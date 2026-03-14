# Generated - extend task_id max_length for timestamp-based format

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("automation", "0006_task_enhancements"),
    ]

    operations = [
        migrations.AlterField(
            model_name="automationtask",
            name="task_id",
            field=models.CharField(
                blank=True,
                help_text="全项目唯一标识，用于追踪。系统自动生成或用户指定，均不可重复。",
                max_length=20,
                unique=True,
                verbose_name="任务ID",
            ),
        ),
    ]
