"""自动化任务视图 - AdminLTE 风格"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.shortcuts import redirect

from .forms import AutomationTaskForm
from .models import AutomationTask


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect("/")


# 可排序列与数据库字段映射
TASK_SORT_FIELDS = {
    "task_id": "task_id",
    "name": "name",
    "task_type": "task_type",
    "status": "status",
    "created_at": "created_at",
    "last_run_at": "last_run_at",
    "organization": "organization__name",
    "created_by": "created_by__username",
}


class AutomationTaskListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = AutomationTask
    template_name = "automation/task_list.html"
    context_object_name = "tasks"
    paginate_by = 20

    def get_queryset(self):
        qs = AutomationTask.objects.select_related(
            "organization", "created_by"
        )
        q = self.request.GET.get("q", "").strip()
        if q:
            from django.db.models import Q
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(task_id__icontains=q)
                | Q(organization__name__icontains=q)
                | Q(created_by__username__icontains=q)
            )
        task_type = self.request.GET.get("task_type")
        if task_type:
            qs = qs.filter(task_type=task_type)
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        org_id = self.request.GET.get("org")
        if org_id:
            qs = qs.filter(organization_id=org_id)
        created_by_id = self.request.GET.get("created_by")
        if created_by_id:
            qs = qs.filter(created_by_id=created_by_id)
        # 排序
        sort_field = self.request.GET.get("sort", "created_at")
        order = self.request.GET.get("order", "desc")
        db_field = TASK_SORT_FIELDS.get(sort_field, "created_at")
        prefix = "" if order == "asc" else "-"
        qs = qs.order_by(prefix + db_field)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["search_q"] = self.request.GET.get("q", "")
        ctx["task_type_filter"] = self.request.GET.get("task_type", "")
        ctx["status_filter"] = self.request.GET.get("status", "")
        ctx["org_filter"] = self.request.GET.get("org", "")
        ctx["created_by_filter"] = self.request.GET.get("created_by", "")
        from apps.organizations.models import Organization
        from django.contrib.auth import get_user_model
        User = get_user_model()
        ctx["organizations"] = Organization.objects.filter(is_active=True).order_by("name")
        # 创建人：有创建过任务的用户 + 当前 staff 用户
        creator_ids = set(
            AutomationTask.objects.exclude(created_by__isnull=True)
            .values_list("created_by_id", flat=True)
            .distinct()
        )
        creators_qs = User.objects.filter(pk__in=creator_ids).order_by("username")
        ctx["creators"] = creators_qs if creators_qs.exists() else User.objects.filter(is_staff=True).order_by("username")[:50]
        ctx["sort_field"] = self.request.GET.get("sort", "created_at")
        ctx["sort_order"] = self.request.GET.get("order", "desc")
        # 构建链接用的 query 参数
        params = self.request.GET.copy()
        for key in ("page", "sort", "order"):
            if key in params:
                del params[key]
        ctx["base_params"] = params.urlencode()  # 排序链接用（不含 sort/order）
        params["sort"] = ctx["sort_field"]
        params["order"] = ctx["sort_order"]
        ctx["query_params"] = params.urlencode()  # 分页链接用（含 sort/order）
        return ctx


class AutomationTaskCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = AutomationTask
    form_class = AutomationTaskForm
    template_name = "automation/task_form.html"
    success_url = reverse_lazy("automation:task_list")
    context_object_name = "task"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "任务创建成功")
        return super().form_valid(form)


class AutomationTaskUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = AutomationTask
    form_class = AutomationTaskForm
    template_name = "automation/task_form.html"
    success_url = reverse_lazy("automation:task_list")
    context_object_name = "task"

    def form_valid(self, form):
        messages.success(self.request, "任务已更新")
        return super().form_valid(form)


class AutomationTaskDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = AutomationTask
    template_name = "automation/task_confirm_delete.html"
    context_object_name = "task"
    success_url = reverse_lazy("automation:task_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "任务已删除")
        return super().delete(request, *args, **kwargs)
