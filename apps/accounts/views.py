"""用户管理视图 - AdminLTE 风格"""
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.shortcuts import redirect

from .forms import UserCreateForm, UserUpdateForm, RoleForm
from .models import Role

User = get_user_model()


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect("/")


class UserListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    paginate_by = 20

    def get_queryset(self):
        qs = User.objects.select_related("profile__organization").order_by("-date_joined")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(username__icontains=q) | qs.filter(email__icontains=q)
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

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["user_obj"] = None
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "用户创建成功")
        return super().form_valid(form)


class UserUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:user_list")
    context_object_name = "user_obj"

    def form_valid(self, form):
        messages.success(self.request, "用户已更新")
        return super().form_valid(form)


class UserDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = User
    template_name = "accounts/user_confirm_delete.html"
    context_object_name = "user_obj"
    success_url = reverse_lazy("accounts:user_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "用户已删除")
        return super().delete(request, *args, **kwargs)


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
