"""自动化任务表单"""
import json
from django import forms
from .models import AutomationTask


class AutomationTaskForm(forms.ModelForm):
    """自动化任务表单"""

    config_json = forms.CharField(
        label="配置 (JSON)",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control font-monospace",
                "rows": 6,
                "placeholder": '{"cron": "0 9 * * *", "target": "https://..."}',
            }
        ),
    )

    class Meta:
        model = AutomationTask
        fields = ["name", "task_type", "organization", "status"]
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

    def clean_config_json(self):
        data = self.cleaned_data.get("config_json", "").strip()
        if not data:
            return {}
        try:
            return json.loads(data)
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f"JSON 格式错误: {e}")

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.config = self.cleaned_data.get("config_json", {})
        if commit:
            obj.save()
        return obj
