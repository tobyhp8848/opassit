"""用户管理视图 - AdminLTE 风格，含审计与软删除"""
import secrets
import string

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.db.models import Q

from .forms import UserCreateForm, UserUpdateForm, RoleForm, UserOrganizationRoleForm
from .models import Role, UserOrganizationRole, UserProfile

User = get_user_model()


def _log_audit(request, action, target_model, target_id, target_repr="", extra=None):
    from apps.audit.models import log_audit
    log_audit(request, action, target_model, target_id, target_repr, extra)


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect("/")


class SuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "仅超级管理员可执行此操作")
        return redirect("/")


class UserListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    paginate_by = 20

    def get_queryset(self):
        qs = User.objects.select_related("profile__organization").order_by("-date_joined")
        # 排除已软删除用户（profile.deleted_at 已设置）
        qs = qs.exclude(profile__deleted_at__isnull=False)
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = (qs.filter(username__icontains=q) | qs.filter(email__icontains=q)).distinct()
        is_active = self.request.GET.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active == "1")
        is_staff = self.request.GET.get("is_staff")
        if is_staff is not None:
            qs = qs.filter(is_staff=is_staff == "1")
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["search_q"] = self.request.GET.get("q", "")
        ctx["is_active_filter"] = self.request.GET.get("is_active", "")
        ctx["is_staff_filter"] = self.request.GET.get("is_staff", "")
        return ctx


class UserCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:user_list")
    context_object_name = "user_obj"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["user_obj"] = None
        return ctx

    def form_valid(self, form):
        resp = super().form_valid(form)
        _log_audit(self.request, "create", "user", self.object.pk, self.object.username)
        messages.success(self.request, "用户创建成功")
        return resp


class UserUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:user_list")
    context_object_name = "user_obj"

    def get_queryset(self):
        # 不允许编辑已软删除用户（需先恢复）
        return User.objects.exclude(profile__deleted_at__isnull=False)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        key = "password_reset_display"
        data = self.request.session.get(key)
        if data and self.object and data.get("username") == self.object.username:
            ctx["password_reset_username"] = data["username"]
            ctx["password_reset_password"] = data["password"]
            del self.request.session[key]
        return ctx

    def form_valid(self, form):
        resp = super().form_valid(form)
        _log_audit(self.request, "update", "user", self.object.pk, self.object.username)
        messages.success(self.request, "用户已更新")
        return resp


def _generate_password(length=12):
    """生成随机密码：字母+数字"""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class UserResetPasswordView(LoginRequiredMixin, StaffRequiredMixin, View):
    """重置用户密码 - 生成随机密码，首次登录须修改"""

    def post(self, request, pk):
        user_obj = get_object_or_404(User, pk=pk)
        # 排除已软删除
        if hasattr(user_obj, "profile") and user_obj.profile and user_obj.profile.deleted_at:
            messages.error(request, "无法重置已删除用户的密码")
            return redirect("accounts:user_edit", pk=pk)
        new_password = _generate_password()
        user_obj.set_password(new_password)
        user_obj.save(update_fields=["password"])
        profile, _ = UserProfile.objects.get_or_create(
            user=user_obj, defaults={"organization": None}
        )
        profile.must_change_password = True
        profile.save(update_fields=["must_change_password"])
        _log_audit(request, "update", "user", user_obj.pk, user_obj.username, extra={"action": "reset_password"})
        request.session["password_reset_display"] = {
            "username": user_obj.username,
            "password": new_password,
        }
        return redirect("accounts:user_edit", pk=pk)


class UserDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    """软删除用户 - 移至已删除用户列表（不进行硬删除）"""
    model = User
    template_name = "accounts/user_confirm_delete.html"
    context_object_name = "user_obj"
    success_url = reverse_lazy("accounts:user_list")

    def get_queryset(self):
        # 可删除的用户：未软删除（profile 不存在或 profile.deleted_at 为空）
        return User.objects.filter(
            Q(profile__isnull=True) | Q(profile__deleted_at__isnull=True)
        ).distinct()

    def post(self, request, *args, **kwargs):
        """重写 post，仅执行软删除，绝不调用父类 delete() 避免硬删除"""
        self.object = self.get_object()
        with transaction.atomic():
            self.object.is_active = False
            self.object.save(update_fields=["is_active"])
            profile, _ = UserProfile.objects.get_or_create(
                user=self.object, defaults={"organization": None}
            )
            UserProfile.objects.filter(pk=profile.pk).update(
                deleted_at=timezone.now(),
                deleted_by_id=request.user.pk,
            )
        _log_audit(request, "delete", "user", self.object.pk, self.object.username)
        messages.success(request, "用户已移至已删除用户列表")
        return redirect(self.success_url)


class UserDeletedListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """已删除用户列表 - 展示 profile.deleted_at 已设置的软删除用户"""
    model = User
    template_name = "accounts/user_deleted.html"
    context_object_name = "users"
    paginate_by = 20

    def get_queryset(self):
        # 直接过滤：有 profile 且 profile.deleted_at 已设置的软删除用户
        return (
            User.objects.filter(profile__deleted_at__isnull=False)
            .select_related("profile", "profile__organization", "profile__deleted_by")
            .order_by("-profile__deleted_at")
        )


class UserRestoreView(LoginRequiredMixin, StaffRequiredMixin, View):
    """恢复已删除用户"""
    success_url = reverse_lazy("accounts:user_deleted_list")

    def post(self, request, pk):
        user_obj = get_object_or_404(User, pk=pk, profile__deleted_at__isnull=False)
        user_obj.is_active = True
        user_obj.save(update_fields=["is_active"])
        profile = user_obj.profile
        profile.deleted_at = None
        profile.deleted_by = None
        profile.save(update_fields=["deleted_at", "deleted_by"])
        _log_audit(request, "restore", "user", user_obj.pk, user_obj.username)
        messages.success(request, "用户已恢复")
        return redirect(self.success_url)


class UserPermanentDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, DeleteView):
    """永久删除用户（仅超级管理员），仅允许删除已软删除的用户"""
    model = User
    template_name = "accounts/user_confirm_permanent_delete.html"
    context_object_name = "user_obj"
    success_url = reverse_lazy("accounts:user_deleted_list")

    def get_queryset(self):
        return User.objects.filter(profile__deleted_at__isnull=False)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        pk, repr_str = self.object.pk, self.object.username
        super().delete(request, *args, **kwargs)
        _log_audit(request, "permanent_delete", "user", pk, repr_str)
        messages.success(request, "用户已永久删除")
        return redirect(self.success_url)


class RoleListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = Role
    template_name = "accounts/role_list.html"
    context_object_name = "roles"
    paginate_by = 20

    def get_queryset(self):
        qs = Role.objects.prefetch_related("permissions").order_by("code")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(name__icontains=q) | qs.filter(code__icontains=q)
        is_system = self.request.GET.get("is_system")
        if is_system is not None:
            qs = qs.filter(is_system=is_system == "1")
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["search_q"] = self.request.GET.get("q", "")
        ctx["is_system_filter"] = self.request.GET.get("is_system", "")
        return ctx


def _role_perm_ids(form, role):
    """获取角色权限 ID 列表，用于表单渲染（含验证失败时保留已选）"""
    if form and form.is_bound and "permissions" in form.data:
        return [int(x) for x in form.data.getlist("permissions") if str(x).isdigit()]
    if role:
        return list(role.permissions.values_list("pk", flat=True))
    return []


def _permissions_grouped(queryset):
    """按 app_label 分组权限"""
    from collections import OrderedDict
    groups = OrderedDict()
    for p in queryset:
        key = getattr(p.content_type, "app_label", "other")
        if key not in groups:
            groups[key] = []
        groups[key].append(p)
    return groups


class RoleCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Role
    form_class = RoleForm
    template_name = "accounts/role_form.html"
    success_url = reverse_lazy("accounts:role_list")
    context_object_name = "role"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["role"] = None
        ctx["role_perm_ids"] = _role_perm_ids(ctx.get("form"), None)
        ctx["permissions_grouped"] = _permissions_grouped(ctx["form"].fields["permissions"].queryset)
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "角色创建成功")
        return super().form_valid(form)


class RoleUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = Role
    form_class = RoleForm
    template_name = "accounts/role_form.html"
    success_url = reverse_lazy("accounts:role_list")
    context_object_name = "role"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["role_perm_ids"] = _role_perm_ids(ctx.get("form"), self.object)
        ctx["permissions_grouped"] = _permissions_grouped(ctx["form"].fields["permissions"].queryset)
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "角色已更新")
        return super().form_valid(form)


class RoleDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Role
    template_name = "accounts/role_confirm_delete.html"
    context_object_name = "role"
    success_url = reverse_lazy("accounts:role_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "角色已删除")
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(is_system=False)


class UserOrganizationRoleListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = UserOrganizationRole
    template_name = "accounts/uor_list.html"
    context_object_name = "assignments"
    paginate_by = 20

    def get_queryset(self):
        qs = UserOrganizationRole.objects.select_related(
            "user", "organization", "role"
        ).order_by("-created_at")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(user__username__icontains=q) | qs.filter(
                organization__name__icontains=q
            )
        org_id = self.request.GET.get("org")
        if org_id:
            qs = qs.filter(organization_id=org_id)
        role_id = self.request.GET.get("role")
        if role_id:
            qs = qs.filter(role_id=role_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from apps.organizations.models import Organization
        ctx["search_q"] = self.request.GET.get("q", "")
        ctx["org_filter"] = self.request.GET.get("org", "")
        ctx["role_filter"] = self.request.GET.get("role", "")
        ctx["organizations"] = Organization.objects.filter(is_active=True).order_by("name")
        ctx["roles"] = Role.objects.order_by("code")
        return ctx


class UserOrganizationRoleCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = UserOrganizationRole
    form_class = UserOrganizationRoleForm
    template_name = "accounts/uor_form.html"
    success_url = reverse_lazy("accounts:uor_list")
    context_object_name = "assignment"

    def form_valid(self, form):
        messages.success(self.request, "分配成功")
        return super().form_valid(form)


class UserOrganizationRoleUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = UserOrganizationRole
    form_class = UserOrganizationRoleForm
    template_name = "accounts/uor_form.html"
    success_url = reverse_lazy("accounts:uor_list")
    context_object_name = "assignment"

    def form_valid(self, form):
        messages.success(self.request, "已更新")
        return super().form_valid(form)


class UserOrganizationRoleDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = UserOrganizationRole
    template_name = "accounts/uor_confirm_delete.html"
    context_object_name = "assignment"
    success_url = reverse_lazy("accounts:uor_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "已取消分配")
        return super().delete(request, *args, **kwargs)
