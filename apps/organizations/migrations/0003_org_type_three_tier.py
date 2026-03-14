# 组织架构简化为 3 层：总公司、子公司、子公司部门

from django.db import migrations, models

# 旧类型 -> 新类型 映射
OLD_TO_NEW = {
    "company": "headquarters",
    "group": "headquarters",
    "subsidiary": "subsidiary",
    "distributor": "department",
    "sub_distributor": "department",
    "third_distributor": "department",
    "fourth_distributor": "department",
}


def migrate_org_types(apps, schema_editor):
    Organization = apps.get_model("organizations", "Organization")
    for old_val, new_val in OLD_TO_NEW.items():
        Organization.objects.filter(org_type=old_val).update(org_type=new_val)
    # 未知类型统一设为 headquarters
    Organization.objects.exclude(
        org_type__in=["headquarters", "subsidiary", "department"]
    ).update(org_type="headquarters")


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0002_org_code_nullable"),
    ]

    operations = [
        migrations.RunPython(migrate_org_types, noop),
        migrations.AlterField(
            model_name="organization",
            name="org_type",
            field=models.CharField(
                choices=[
                    ("headquarters", "总公司"),
                    ("subsidiary", "子公司"),
                    ("department", "子公司部门"),
                ],
                default="headquarters",
                max_length=20,
                verbose_name="组织类型",
            ),
        ),
    ]
