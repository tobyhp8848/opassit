"""自动化任务表单"""
import json
from django import forms
from .models import AutomationTask, TaskAttachment

# Cron 周几：0=周日, 1=周一, ..., 6=周六
WEEKDAY_CHOICES = [(str(i), name) for i, name in enumerate(["周日", "周一", "周二", "周三", "周四", "周五", "周六"])]
RECURRENCE_PRESET_CHOICES = [
    ("daily", "每天固定时间"),
    ("weekly", "每周指定日期"),
    ("custom", "自定义 Cron 表达式"),
]


class AutomationTaskForm(forms.ModelForm):
    """自动化任务表单"""

    config_json = forms.CharField(
        label="配置 (JSON)",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control font-monospace",
                "rows": 4,
                "placeholder": '{"target": "https://..."}',
            }
        ),
    )
    description = forms.CharField(
        label="任务详细说明",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "请简要描述任务目的、步骤、预期结果等",
            }
        ),
    )
    schedule_type = forms.ChoiceField(
        label="执行类型",
        choices=AutomationTask.ScheduleType.choices,
        required=True,
        initial="once",
        widget=forms.RadioSelect(attrs={"class": "schedule-type-radio"}),
    )
    scheduled_run_at = forms.DateTimeField(
        label="计划执行时间",
        required=False,
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"],
        widget=forms.DateTimeInput(
            attrs={
                "type": "datetime-local",
                "class": "form-control",
            },
            format="%Y-%m-%dT%H:%M",
        ),
    )
    cron_expression = forms.CharField(
        label="Cron 表达式",
        required=False,
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "0 9 * * *  (每天 9:00)",
            }
        ),
    )
    recurrence_preset = forms.ChoiceField(
        label="周期类型",
        choices=RECURRENCE_PRESET_CHOICES,
        required=False,
        initial="daily",
        widget=forms.RadioSelect(attrs={"class": "recurrence-preset-radio"}),
    )
    recurrence_weekdays = forms.MultipleChoiceField(
        label="执行日期（周几）",
        choices=WEEKDAY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "recurrence-weekday-check"}),
    )
    recurrence_time = forms.TimeField(
        label="执行时间",
        required=False,
        input_formats=["%H:%M", "%H:%M:%S"],
        widget=forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
    )

    class Meta:
        model = AutomationTask
        fields = ["name", "task_type", "organization", "status", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "任务名称"}),
            "task_type": forms.Select(attrs={"class": "form-control"}),
            "organization": forms.Select(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.organizations.models import Organization

        self.fields["organization"].queryset = Organization.objects.filter(is_active=True).order_by("name")
        self.fields["organization"].required = False
        if self.instance and self.instance.pk:
            self.fields["config_json"].initial = (
                json.dumps(self.instance.config, ensure_ascii=False, indent=2)
                if self.instance.config
                else "{}"
            )
            self.fields["description"].initial = self.instance.description or ""
            self.fields["schedule_type"].initial = getattr(
                self.instance, "schedule_type", "once"
            ) or "once"
            self.fields["scheduled_run_at"].initial = (
                self.instance.scheduled_run_at.strftime("%Y-%m-%dT%H:%M")
                if self.instance.scheduled_run_at
                else None
            )
            self.fields["cron_expression"].initial = self.instance.cron_expression or ""
            cfg = self.instance.config or {}
            cron = (self.instance.cron_expression or "").strip()
            # 从 config 或 cron 反推预设
            preset = cfg.get("recurrence_preset")
            if not preset and cron:
                parts = cron.split()
                if len(parts) >= 5 and parts[4] not in ("*", ""):
                    preset = "weekly" if "," in parts[4] or "-" in parts[4] else "daily"
                else:
                    preset = "custom"
            self.fields["recurrence_preset"].initial = preset or "daily"
            self.fields["recurrence_weekdays"].initial = cfg.get("recurrence_weekdays") or self._parse_weekdays_from_cron(cron)
            self.fields["recurrence_time"].initial = cfg.get("recurrence_time") or self._parse_time_from_cron(cron)
        else:
            self.fields["schedule_type"].initial = "once"
            self.fields["recurrence_preset"].initial = "daily"

    def clean_config_json(self):
        data = self.cleaned_data.get("config_json", "").strip()
        if not data:
            return {}
        try:
            return json.loads(data)
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f"JSON 格式错误: {e}")

    def clean_scheduled_run_at(self):
        val = self.cleaned_data.get("scheduled_run_at")
        if val and self.cleaned_data.get("schedule_type") == "once":
            return val
        return val

    def clean(self):
        data = super().clean()
        if data.get("schedule_type") == "recurring":
            preset = data.get("recurrence_preset")
            weekdays = data.get("recurrence_weekdays") or []
            if preset == "weekly" and not weekdays:
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    {"recurrence_weekdays": "请至少选择一个执行日期（周几）"}
                )
        return data

    def _parse_time_from_cron(self, cron):
        """从 cron 提取时间，返回 'HH:MM' 或 None"""
        if not cron:
            return None
        parts = cron.split()
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            return f"{int(parts[1]):02d}:{int(parts[0]):02d}"
        return None

    def _parse_weekdays_from_cron(self, cron):
        """从 cron 提取周几，返回 ['0','1',...] 或 []"""
        if not cron:
            return []
        parts = cron.split()
        if len(parts) < 5 or parts[4] in ("*", ""):
            return []
        wd = parts[4]
        out = []
        for bit in wd.replace("-", ",").split(","):
            bit = bit.strip()
            if bit.isdigit() and 0 <= int(bit) <= 6:
                out.append(bit)
        return list(dict.fromkeys(out))  # 去重保序

    def _build_cron_from_preset(self, preset, weekdays, time_val):
        """从预设构建 cron 表达式。Cron: 分 时 日 月 周(0=周日,1=周一,...,6=周六)"""
        if not time_val:
            return ""
        h, m = time_val.hour, time_val.minute
        if preset == "daily":
            return f"{m} {h} * * *"
        if preset == "weekly" and weekdays:
            wd = ",".join(sorted(weekdays))  # "0,1,2" 等
            return f"{m} {h} * * {wd}"
        return ""

    def save(self, commit=True):
        obj = super().save(commit=False)
        config = self.cleaned_data.get("config_json") or {}
        if not isinstance(config, dict):
            config = {}
        obj.description = self.cleaned_data.get("description", "")
        obj.schedule_type = self.cleaned_data.get("schedule_type", "once")
        obj.scheduled_run_at = self.cleaned_data.get("scheduled_run_at")

        preset = self.cleaned_data.get("recurrence_preset")
        weekdays = self.cleaned_data.get("recurrence_weekdays") or []
        time_val = self.cleaned_data.get("recurrence_time")
        custom_cron = (self.cleaned_data.get("cron_expression") or "").strip()

        if obj.schedule_type == "recurring":
            built = self._build_cron_from_preset(preset, weekdays, time_val)
            if preset == "custom" and custom_cron:
                obj.cron_expression = custom_cron
            elif built:
                obj.cron_expression = built
            else:
                obj.cron_expression = custom_cron or "0 9 * * *"

            config["recurrence_preset"] = preset
            config["recurrence_weekdays"] = weekdays
            config["recurrence_time"] = time_val.strftime("%H:%M") if time_val else None
        else:
            obj.cron_expression = ""

        obj.config = config
        if commit:
            obj.save()
        return obj
