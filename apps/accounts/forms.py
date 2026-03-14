"""用户管理表单"""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import UserProfile, Role, UserOrganizationRole

User = get_user_model()


class UserOrganizationRoleForm(forms.ModelForm):
    """用户-组织-角色 关联表单"""

    class Meta:
        model = UserOrganizationRole
        fields = ["user", "organization", "role", "is_primary"]
        widgets = {
            "user": forms.Select(attrs={"class": "form-control"}),
            "organization": forms.Select(attrs={"class": "form-control"}),
            "role": forms.Select(attrs={"class": "form-control"}),
            "is_primary": forms.CheckboxInput(attrs={"class": "custom-control-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.organizations.models import Organization
        self.fields["user"].queryset = User.objects.filter(is_active=True).order_by("username")
        self.fields["organization"].queryset = Organization.objects.filter(is_active=True).order_by("name")
        self.fields["role"].queryset = Role.objects.order_by("code")

    def clean(self):
        data = super().clean()
        user = data.get("user")
        org = data.get("organization")
        role = data.get("role")
        if user and org and role:
            qs = UserOrganizationRole.objects.filter(user=user, organization=org, role=role)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("该用户在此组织中已拥有此角色，请勿重复添加。")
        return data


class UserCreateForm(UserCreationForm):
    """新建用户"""

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "is_staff", "is_active", "is_superuser"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
        }

    organization = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label="主组织",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    phone = forms.CharField(max_length=20, required=False, label="手机号", widget=forms.TextInput(attrs={"class": "form-control"}))

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        from apps.organizations.models import Organization
        self.fields["organization"].queryset = Organization.objects.filter(is_active=True).order_by("name")
        for f in ["username", "email", "password1", "password2"]:
            if f in self.fields and hasattr(self.fields[f], "widget"):
                self.fields[f].widget.attrs.setdefault("class", "form-control")
        if not self.instance or not self.instance.pk:
            self.fields["is_staff"].initial = False
            self.fields["is_superuser"].initial = False
        self.fields["is_staff"].required = False
        self.fields["is_superuser"].required = False

    def save(self, commit=True):
        user = super().save(commit=False)
        # 直接从 request.POST 读取复选框，避免 HTML 复选框未勾选不提交导致的绑定问题
        if self.request and self.request.method == "POST":
            user.is_staff = self.request.POST.get("is_staff") == "1"
            user.is_superuser = self.request.POST.get("is_superuser") == "1"
        else:
            user.is_staff = bool(self.cleaned_data.get("is_staff", False))
            user.is_superuser = bool(self.cleaned_data.get("is_superuser", False))
        if commit:
            user.save()
            UserProfile.objects.update_or_create(user=user, defaults={
                "organization": self.cleaned_data.get("organization"),
                "phone": self.cleaned_data.get("phone", "") or "",
            })
        return user


class UserUpdateForm(forms.ModelForm):
    """编辑用户"""

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "is_staff", "is_active", "is_superuser"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
        }

    organization = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label="主组织",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    phone = forms.CharField(max_length=20, required=False, label="手机号", widget=forms.TextInput(attrs={"class": "form-control"}))

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        from apps.organizations.models import Organization
        self.fields["organization"].queryset = Organization.objects.filter(is_active=True).order_by("name")
        self.fields["is_staff"].required = False
        self.fields["is_superuser"].required = False
        self.fields["is_active"].required = False
        try:
            profile = self.instance.profile
        except UserProfile.DoesNotExist:
            profile = None
        if profile:
            self.fields["organization"].initial = profile.organization_id
            self.fields["phone"].initial = profile.phone

    def save(self, commit=True):
        user = super().save(commit=False)
        # 直接从 request.POST 读取复选框值，避免 HTML 复选框未勾选不提交导致的绑定问题
        if self.request and self.request.method == "POST":
            user.is_staff = self.request.POST.get("is_staff") == "1"
            user.is_superuser = self.request.POST.get("is_superuser") == "1"
            user.is_active = self.request.POST.get("is_active", "1") == "1"
        else:
            user.is_staff = bool(self.cleaned_data.get("is_staff", False))
            user.is_superuser = bool(self.cleaned_data.get("is_superuser", False))
        if commit:
            user.save()
            # 仅更新 organization、phone，绝不触碰 deleted_at/deleted_by（软删除字段）
            defaults = {
                "organization": self.cleaned_data.get("organization"),
                "phone": self.cleaned_data.get("phone", "") or "",
            }
            UserProfile.objects.update_or_create(user=user, defaults=defaults)
        return user


class RoleForm(forms.ModelForm):
    """角色表单"""

    class Meta:
        model = Role
        fields = ["name", "code", "description", "is_system", "permissions"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "permissions": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth.models import Permission
        self.fields["permissions"].queryset = Permission.objects.select_related("content_type").order_by("content_type__app_label", "content_type__model", "codename")
