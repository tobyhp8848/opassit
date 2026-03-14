"""自动化任务视图 - AdminLTE 风格，含审计与软删除"""
import calendar
from datetime import date, datetime, timedelta, time

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View, DetailView
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Q, Subquery, OuterRef, Count, Value, IntegerField
from django.db.models.functions import Coalesce

from .forms import AutomationTaskForm
from .models import AutomationTask, TaskAttachment, TaskRemark


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


def _task_list_queryset_base(exclude_deleted=True):
    qs = AutomationTask.objects.select_related("organization", "created_by", "approved_by", "deleted_by", "assigned_to")
    if exclude_deleted:
        qs = qs.filter(is_deleted=False)
    return qs


def _task_list_context(view, ctx):
    from apps.organizations.models import Organization
    from django.contrib.auth import get_user_model
    User = get_user_model()
    ctx["search_q"] = view.request.GET.get("q", "").strip()
    ctx["task_type_filter"] = view.request.GET.get("task_type", "")
    ctx["status_filter"] = view.request.GET.get("status", "")
    ctx["approval_status_filter"] = view.request.GET.get("approval_status", "")
    org_raw = view.request.GET.get("org", "").strip()
    created_raw = view.request.GET.get("created_by", "").strip()
    ctx["org_filter"] = str(int(org_raw)) if org_raw.isdigit() and int(org_raw) > 0 else ""
    ctx["created_by_filter"] = str(int(created_raw)) if created_raw.isdigit() and int(created_raw) > 0 else ""
    orgs_list = list(Organization.objects.filter(is_active=True).order_by("name"))
    if ctx["org_filter"]:
        try:
            pk = int(ctx["org_filter"])
            if not any(o.pk == pk for o in orgs_list):
                extra = Organization.objects.filter(pk=pk).first()
                if extra:
                    orgs_list.insert(0, extra)
        except (ValueError, TypeError):
            pass
    ctx["organizations"] = orgs_list
    base = _task_list_queryset_base(exclude_deleted=True)
    creator_ids = set(base.exclude(created_by__isnull=True).values_list("created_by_id", flat=True).distinct())
    creators_qs = User.objects.filter(pk__in=creator_ids).order_by("username") if creator_ids else User.objects.none()
    creators_list = list(creators_qs)
    if not creators_list:
        creators_list = list(User.objects.filter(is_staff=True, is_active=True).order_by("username")[:50])
    if ctx["created_by_filter"]:
        try:
            pk = int(ctx["created_by_filter"])
            if not any(u.pk == pk for u in creators_list):
                extra_user = User.objects.filter(pk=pk).first()
                if extra_user:
                    creators_list.insert(0, extra_user)
        except (ValueError, TypeError):
            pass
    ctx["creators"] = creators_list
    ctx["sort_field"] = view.request.GET.get("sort", "created_at")
    ctx["sort_order"] = view.request.GET.get("order", "desc")
    params = view.request.GET.copy()
    for key in ("page", "sort", "order"):
        if key in params:
            del params[key]
    ctx["base_params"] = params.urlencode()
    params["sort"] = ctx["sort_field"]
    params["order"] = ctx["sort_order"]
    ctx["query_params"] = params.urlencode()
    return ctx


class AutomationTaskListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """任务列表 - 所有未删除任务（含各审批状态）"""
    model = AutomationTask
    template_name = "automation/task_list.html"
    context_object_name = "tasks"
    paginate_by = 20

    def get_queryset(self):
        from apps.audit.models import AuditLog

        qs = _task_list_queryset_base(exclude_deleted=True)
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(name__icontains=q) | Q(task_id__icontains=q)
                | Q(organization__name__icontains=q) | Q(created_by__username__icontains=q)
            )
        for key, val in [
            ("task_type", "task_type"),
            ("status", "status"),
            ("approval_status", "approval_status"),
            ("org", "organization_id"),
            ("created_by", "created_by_id"),
        ]:
            v = self.request.GET.get(key)
            if v:
                v = v.strip()
                if val in ("organization_id", "created_by_id"):
                    if not v.isdigit() or int(v) <= 0:
                        continue
                qs = qs.filter(**{val: v})
        # 注解：任务被执行次数
        exec_count_subq = AuditLog.objects.filter(
            target_model="automation_task",
            target_id=OuterRef("pk"),
            action="execute",
        ).order_by().values("target_id").annotate(c=Count("id")).values("c")[:1]
        qs = qs.annotate(
            execution_count=Coalesce(Subquery(exec_count_subq), Value(0), output_field=IntegerField())
        )
        sort_field = self.request.GET.get("sort", "created_at")
        order = self.request.GET.get("order", "desc")
        db_field = TASK_SORT_FIELDS.get(sort_field, "created_at")
        prefix = "" if order == "asc" else "-"
        return qs.order_by(prefix + db_field)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return _task_list_context(self, ctx)


def _save_task_attachments(request, task, remark=""):
    """保存上传的附件到任务"""
    files = list(request.FILES.getlist("attachments")) + list(request.FILES.getlist("folder_files"))
    for f in files:
        if f.size > 0:
            TaskAttachment.objects.create(task=task, file=f, remark=remark)


class AutomationTaskCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    """提交任务"""
    model = AutomationTask
    form_class = AutomationTaskForm
    template_name = "automation/task_form.html"
    success_url = reverse_lazy("automation:task_list")
    context_object_name = "task"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.approval_status = AutomationTask.ApprovalStatus.PENDING
        resp = super().form_valid(form)
        remark = self.request.POST.get("attachment_remark", "").strip()
        _save_task_attachments(self.request, self.object, remark)
        _log_audit(self.request, "create", "automation_task", self.object.pk, str(self.object))
        messages.success(self.request, "任务已提交，等待审批")
        return resp


class AutomationTaskUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = AutomationTask
    form_class = AutomationTaskForm
    template_name = "automation/task_form.html"
    success_url = reverse_lazy("automation:task_list")
    context_object_name = "task"

    def get_queryset(self):
        return AutomationTask.objects.filter(is_deleted=False).prefetch_related("attachments")

    def form_valid(self, form):
        resp = super().form_valid(form)
        remark = self.request.POST.get("attachment_remark", "").strip()
        _save_task_attachments(self.request, self.object, remark)
        _log_audit(self.request, "update", "automation_task", self.object.pk, str(self.object))
        messages.success(self.request, "任务已更新")
        return resp


class AutomationTaskBatchActionView(LoginRequiredMixin, StaffRequiredMixin, View):
    """批量操作：审批、执行、软删除"""
    def post(self, request):
        ids = request.POST.getlist("ids")
        if not ids:
            messages.warning(request, "请至少选择一个任务")
            return redirect(request.POST.get("next") or reverse_lazy("automation:task_list"))
        try:
            pks = [int(x) for x in ids if x]
        except (ValueError, TypeError):
            messages.error(request, "无效的任务 ID")
            return redirect(request.POST.get("next") or reverse_lazy("automation:task_list"))

        action = request.POST.get("action", "").strip()
        tasks = AutomationTask.objects.filter(pk__in=pks, is_deleted=False)

        if action == "approve":
            status = (request.POST.get("status") or "").strip().lower()
            if status not in APPROVAL_STATUS_MAP:
                messages.error(
                    request,
                    "无效的审批状态。请选择：待审核、审批通过、指派人员构建工作、指派任务完成、任务可执行、已驳回、被取消"
                )
                return redirect(request.POST.get("next") or reverse_lazy("automation:task_list"))
            for t in tasks:
                t.approval_status = status
                t.approved_at = timezone.now()
                t.approved_by = request.user
                t.save(update_fields=["approval_status", "approved_at", "approved_by", "updated_at"])
                audit_action = AUDIT_ACTION_MAP.get(status, "update")
                extra = {"approval_status": status} if status == "pending" else None
                _log_audit(request, audit_action, "automation_task", t.pk, str(t), extra=extra)
            label = APPROVAL_STATUS_MAP[status][0]
            messages.success(request, f"已将 {tasks.count()} 个任务批量设为「{label}」")
        elif action == "execute":
            executable_tasks = tasks.filter(approval_status=AutomationTask.ApprovalStatus.EXECUTABLE)
            for t in executable_tasks:
                t.last_run_at = timezone.now()
                t.save(update_fields=["last_run_at", "updated_at"])
                _log_audit(request, "execute", "automation_task", t.pk, str(t))
            skipped = tasks.count() - executable_tasks.count()
            if executable_tasks.count() > 0:
                msg = f"已记录 {executable_tasks.count()} 个任务执行"
                if skipped > 0:
                    msg += f"，{skipped} 个非可执行状态已跳过"
                messages.success(request, msg)
            else:
                messages.warning(request, "所选任务均非「任务可执行」状态，无法执行")
        elif action == "delete":
            for t in tasks:
                t.is_deleted = True
                t.deleted_at = timezone.now()
                t.deleted_by = request.user
                t.save(update_fields=["is_deleted", "deleted_at", "deleted_by", "updated_at"])
                _log_audit(request, "delete", "automation_task", t.pk, str(t))
            messages.success(request, f"已将 {tasks.count()} 个任务移至已删除列表")
        else:
            messages.error(request, "无效的批量操作")
        next_url = request.POST.get("next") or reverse_lazy("automation:task_list")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return redirect(reverse_lazy("automation:task_list"))


class AutomationTaskDeleteView(LoginRequiredMixin, StaffRequiredMixin, View):
    """软删除任务"""
    def post(self, request, pk):
        task = get_object_or_404(AutomationTask, pk=pk, is_deleted=False)
        task.is_deleted = True
        task.deleted_at = timezone.now()
        task.deleted_by = request.user
        task.save(update_fields=["is_deleted", "deleted_at", "deleted_by", "updated_at"])
        _log_audit(request, "delete", "automation_task", task.pk, str(task))
        messages.success(request, "任务已移至已删除列表")
        next_url = request.POST.get("next") or request.GET.get("next")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return redirect(reverse_lazy("automation:task_list"))

    def get(self, request, pk):
        task = get_object_or_404(AutomationTask, pk=pk, is_deleted=False)
        from django.shortcuts import render
        return render(request, "automation/task_confirm_delete.html", {"task": task})


def _build_calendar_context(year, month, tasks_qs, sel_start=None, sel_end=None, is_range=False):
    """构建当月日历数据及按日期分组的任务，标记选中状态"""
    cal = calendar.monthcalendar(year, month)
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])

    tasks_by_date = {}
    for t in tasks_qs:
        if t.scheduled_run_at:
            d = t.scheduled_run_at.date()
            if first_day <= d <= last_day:
                key = d.isoformat()
                tasks_by_date.setdefault(key, []).append(t)

    def _is_selected(d_str):
        if not sel_start or not d_str:
            return False
        try:
            d = date.fromisoformat(d_str)
            if is_range and sel_end:
                return sel_start <= d <= sel_end
            return d == sel_start
        except (ValueError, TypeError):
            return False

    def _is_in_range(d_str):
        if not is_range or not sel_start or not sel_end or not d_str:
            return False
        try:
            d = date.fromisoformat(d_str)
            return sel_start <= d <= sel_end
        except (ValueError, TypeError):
            return False

    # 计算首个 “1” 的位置，用于推算其他月份格子的日期
    first_1_col = None
    for wi, week in enumerate(cal):
        for ci, day in enumerate(week):
            if day == 1:
                first_1_col = wi * 7 + ci
                break
        if first_1_col is not None:
            break

    calendar_grid = []
    for wi, week in enumerate(cal):
        row = []
        for ci, day in enumerate(week):
            cell_index = wi * 7 + ci
            if day == 0:
                date_str = None
                other_day = None
                if first_1_col is not None:
                    offset = cell_index - first_1_col
                    from datetime import timedelta
                    d = first_day + timedelta(days=offset)
                    date_str = d.isoformat()
                    other_day = d.day
                row.append({
                    "day": other_day,
                    "date_str": date_str,
                    "tasks": tasks_by_date.get(date_str, []) if date_str else [],
                    "is_other": True,
                    "is_selected": _is_selected(date_str) if date_str else False,
                    "is_in_range": _is_in_range(date_str) if date_str else False,
                })
            else:
                date_str = f"{year:04d}-{month:02d}-{day:02d}"
                row.append({
                    "day": day,
                    "date_str": date_str,
                    "tasks": tasks_by_date.get(date_str, []),
                    "is_other": False,
                    "is_selected": _is_selected(date_str),
                    "is_in_range": _is_in_range(date_str),
                })
        calendar_grid.append(row)

    return {
        "calendar_grid": calendar_grid,
        "calendar_year": year,
        "calendar_month": month,
        "calendar_month_name": f"{year}年{month}月",
        "weekday_headers": ["日", "一", "二", "三", "四", "五", "六"],
    }


def _parse_date_selection(request):
    """
    解析日期选择：date(单日) 或 start+end(范围)。
    默认当天；若当天不在当前月则取当月1日。
    """
    today = date.today()
    year = int(request.GET.get("year") or today.year)
    month = int(request.GET.get("month") or today.month)
    if month > 12:
        month, year = 12, year
    elif month < 1:
        month, year = 1, year - 1

    date_param = request.GET.get("date", "").strip()
    start_param = request.GET.get("start", "").strip()
    end_param = request.GET.get("end", "").strip()

    if date_param:
        try:
            sel = date.fromisoformat(date_param)
            return year, month, sel, sel, False  # single day
        except (ValueError, TypeError):
            pass
    if start_param and end_param:
        try:
            start_d = date.fromisoformat(start_param)
            end_d = date.fromisoformat(end_param)
            if start_d <= end_d:
                return year, month, start_d, end_d, True  # range
        except (ValueError, TypeError):
            pass

    # 默认：当天；若不在当前 calendar 月内，用当月1日
    first = date(year, month, 1)
    last = date(year, month, calendar.monthrange(year, month)[1])
    if first <= today <= last:
        default_d = today
    else:
        default_d = first
    return year, month, default_d, default_d, False


class AutomationTaskBoardView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """任务看板 - 左侧当月日历，右侧任务列表，支持单日/范围选择，默认当天"""
    model = AutomationTask
    template_name = "automation/task_board.html"
    context_object_name = "tasks"
    paginate_by = 999

    def get_queryset(self):
        qs = _task_list_queryset_base(exclude_deleted=True)
        qs = qs.select_related("organization", "created_by", "approved_by")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(task_id__icontains=q))
        status_filter = self.request.GET.get("approval_status", "")
        if status_filter:
            qs = qs.filter(approval_status=status_filter)

        _, _, sel_start, sel_end, is_range = _parse_date_selection(self.request)
        qs = qs.filter(scheduled_run_at__isnull=False)
        # 使用时区-aware 的 datetime 范围过滤，避免 __date 在 UTC 下导致日期错位
        tz = timezone.get_current_timezone()
        start_dt = timezone.make_aware(datetime.combine(sel_start, time.min), tz)
        end_dt = timezone.make_aware(datetime.combine(sel_end, time.max), tz)
        qs = qs.filter(
            scheduled_run_at__gte=start_dt,
            scheduled_run_at__lte=end_dt,
        )
        return qs.order_by("scheduled_run_at")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = date.today()
        year, month, sel_start, sel_end, is_range = _parse_date_selection(self.request)
        ctx["calendar_year"] = year
        ctx["calendar_month"] = month
        ctx["sel_start"] = sel_start
        ctx["sel_end"] = sel_end
        ctx["is_range"] = is_range
        ctx["sel_start_str"] = sel_start.isoformat()
        ctx["sel_end_str"] = sel_end.isoformat()
        ctx["prev_month"] = (month - 1) or 12
        ctx["prev_year"] = year if month > 1 else year - 1
        ctx["next_month"] = (month % 12) + 1
        ctx["next_year"] = year if month < 12 else year + 1
        from urllib.parse import urlencode
        base_get = {
            "year": year,
            "month": month,
        }
        if self.request.GET.get("q"):
            base_get["q"] = self.request.GET.get("q")
        if self.request.GET.get("approval_status"):
            base_get["approval_status"] = self.request.GET.get("approval_status")
        ctx["base_query"] = urlencode(base_get)
        ctx["is_today"] = today.year == year and today.month == month
        ctx["today_day"] = today.day if ctx["is_today"] else None
        ctx.update(_build_calendar_context(
            year, month, self._get_all_tasks_for_calendar(),
            sel_start=sel_start, sel_end=sel_end, is_range=is_range,
        ))
        return ctx

    def _get_all_tasks_for_calendar(self):
        """日历上展示任务用，不受日期筛选影响"""
        qs = _task_list_queryset_base(exclude_deleted=True)
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(task_id__icontains=q))
        status_filter = self.request.GET.get("approval_status", "")
        if status_filter:
            qs = qs.filter(approval_status=status_filter)
        return qs


class AutomationTaskPendingListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """待审核任务"""
    model = AutomationTask
    template_name = "automation/task_pending.html"
    context_object_name = "tasks"
    paginate_by = 20

    def get_queryset(self):
        return _task_list_queryset_base(exclude_deleted=True).filter(
            approval_status=AutomationTask.ApprovalStatus.PENDING
        ).select_related("organization", "created_by").order_by("-created_at")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["organizations"] = __import__("apps.organizations.models", fromlist=["Organization"]).Organization.objects.filter(is_active=True).order_by("name")
        return ctx


class AutomationTaskAssignBuildListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """待指派人员构建工作 - 审批通过(approved)等待指派，或已指派(assign_build)构建中，排除已完成"""
    model = AutomationTask
    template_name = "automation/task_assign_build_list.html"
    context_object_name = "tasks"
    paginate_by = 20

    def get_queryset(self):
        from django.db.models import Q
        return _task_list_queryset_base(exclude_deleted=True).filter(
            Q(approval_status=AutomationTask.ApprovalStatus.APPROVED) |
            Q(approval_status=AutomationTask.ApprovalStatus.ASSIGN_BUILD)
        ).exclude(build_status=AutomationTask.BuildStatus.COMPLETED).select_related(
            "organization", "created_by", "assigned_to"
        ).order_by("-updated_at")

    def get_context_data(self, **kwargs):
        from django.contrib.auth import get_user_model
        ctx = super().get_context_data(**kwargs)
        ctx["staff_users"] = get_user_model().objects.filter(is_staff=True, is_active=True).order_by("username")
        return ctx


class AutomationTaskBuildAcceptanceListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """待构建工作验收 - approval_status=assign_build 且 build_status=completed"""
    model = AutomationTask
    template_name = "automation/task_build_acceptance_list.html"
    context_object_name = "tasks"
    paginate_by = 20

    def get_queryset(self):
        return _task_list_queryset_base(exclude_deleted=True).filter(
            approval_status=AutomationTask.ApprovalStatus.ASSIGN_BUILD,
            build_status=AutomationTask.BuildStatus.COMPLETED
        ).select_related("organization", "created_by", "assigned_to").order_by("-updated_at")


class AutomationTaskExecutableListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """可执行任务 - 审批状态为「任务可执行」的所有任务"""
    model = AutomationTask
    template_name = "automation/task_executable_list.html"
    context_object_name = "tasks"
    paginate_by = 20

    def get_queryset(self):
        return _task_list_queryset_base(exclude_deleted=True).filter(
            approval_status=AutomationTask.ApprovalStatus.EXECUTABLE
        ).select_related("organization", "created_by", "assigned_to").order_by("-updated_at")


class AutomationTaskSetBuildStatusView(LoginRequiredMixin, StaffRequiredMixin, View):
    """被指派人员设置构建状态：接受任务、构建工作进行中、构建工作完成、退回再修改"""
    BUILD_STATUS_MAP = {
        "accepted": ("接受任务", "info"),
        "in_progress": ("构建工作进行中", "primary"),
        "completed": ("构建工作完成", "success"),
        "return_revision": ("退回再修改", "warning"),
    }

    def post(self, request, pk):
        task = get_object_or_404(
            AutomationTask,
            pk=pk,
            is_deleted=False,
            approval_status=AutomationTask.ApprovalStatus.ASSIGN_BUILD,
        )
        status = (request.POST.get("build_status") or "").strip().lower()
        if status not in self.BUILD_STATUS_MAP:
            messages.error(request, "无效的构建状态")
            return redirect(request.POST.get("next") or reverse_lazy("automation:task_assign_build_list"))
        if task.assigned_to and task.assigned_to != request.user and not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, "仅被指派人员或管理员可操作")
            return redirect(request.POST.get("next") or reverse_lazy("automation:task_assign_build_list"))
        task.build_status = status
        task.save(update_fields=["build_status", "updated_at"])
        _log_audit(request, "update", "automation_task", task.pk, str(task), extra={"build_status": status})
        label = self.BUILD_STATUS_MAP[status][0]
        messages.success(request, f"已设为「{label}」")
        next_url = request.POST.get("next") or reverse_lazy("automation:task_assign_build_list")
        if next_url.startswith("/"):
            return redirect(next_url)
        return redirect(reverse_lazy("automation:task_assign_build_list"))


class AutomationTaskAssignUserView(LoginRequiredMixin, StaffRequiredMixin, View):
    """指派构建人员 - 支持 approved 或 assign_build 状态的任务"""

    def post(self, request, pk):
        task = get_object_or_404(
            AutomationTask,
            pk=pk,
            is_deleted=False,
        )
        if task.approval_status not in (
            AutomationTask.ApprovalStatus.APPROVED,
            AutomationTask.ApprovalStatus.ASSIGN_BUILD,
        ):
            messages.error(request, "仅审批通过或指派构建中的任务可进行指派")
            return redirect(request.POST.get("next") or reverse_lazy("automation:task_assign_build_list"))
        if task.build_status == AutomationTask.BuildStatus.COMPLETED:
            messages.error(request, "已完成构建的任务不可变更指派")
            return redirect(request.POST.get("next") or reverse_lazy("automation:task_assign_build_list"))
        from django.contrib.auth import get_user_model
        uid = request.POST.get("assigned_to")
        update_fields = ["assigned_to", "updated_at"]
        if uid:
            user = get_user_model().objects.filter(pk=int(uid), is_active=True).first()
            if user:
                task.assigned_to = user
                if task.approval_status == AutomationTask.ApprovalStatus.APPROVED:
                    task.approval_status = AutomationTask.ApprovalStatus.ASSIGN_BUILD
                    update_fields.append("approval_status")
                task.save(update_fields=update_fields)
                _log_audit(request, "update", "automation_task", task.pk, str(task), extra={"assigned_to": user.username})
                messages.success(request, f"已指派给 {user.username}")
        else:
            task.assigned_to = None
            if task.approval_status == AutomationTask.ApprovalStatus.ASSIGN_BUILD and not task.build_status:
                task.approval_status = AutomationTask.ApprovalStatus.APPROVED
                update_fields.append("approval_status")
            task.save(update_fields=update_fields)
            messages.success(request, "已清除指派")
        next_url = request.POST.get("next") or reverse_lazy("automation:task_assign_build_list")
        return redirect(next_url if next_url.startswith("/") else reverse_lazy("automation:task_assign_build_list"))


class AutomationTaskBatchAssignView(LoginRequiredMixin, StaffRequiredMixin, View):
    """批量指派构建人员"""

    def post(self, request):
        ids = request.POST.getlist("ids")
        if not ids:
            messages.warning(request, "请至少选择一个任务")
            return redirect(request.POST.get("next") or reverse_lazy("automation:task_assign_build_list"))
        try:
            pks = [int(x) for x in ids if x]
        except (ValueError, TypeError):
            messages.error(request, "无效的任务 ID")
            return redirect(request.POST.get("next") or reverse_lazy("automation:task_assign_build_list"))
        from django.contrib.auth import get_user_model
        uid = request.POST.get("assigned_to")
        if not uid:
            messages.warning(request, "请选择要指派的用户")
            return redirect(request.POST.get("next") or reverse_lazy("automation:task_assign_build_list"))
        user = get_user_model().objects.filter(pk=int(uid), is_active=True).first()
        if not user:
            messages.error(request, "无效的指派用户")
            return redirect(request.POST.get("next") or reverse_lazy("automation:task_assign_build_list"))
        tasks = AutomationTask.objects.filter(
            pk__in=pks,
            is_deleted=False,
        ).filter(
            Q(approval_status=AutomationTask.ApprovalStatus.APPROVED) |
            Q(approval_status=AutomationTask.ApprovalStatus.ASSIGN_BUILD)
        ).exclude(build_status=AutomationTask.BuildStatus.COMPLETED)
        for t in tasks:
            t.assigned_to = user
            if t.approval_status == AutomationTask.ApprovalStatus.APPROVED:
                t.approval_status = AutomationTask.ApprovalStatus.ASSIGN_BUILD
            t.save(update_fields=["assigned_to", "approval_status", "updated_at"])
            _log_audit(request, "update", "automation_task", t.pk, str(t), extra={"assigned_to": user.username})
        messages.success(request, f"已将 {tasks.count()} 个任务批量指派给 {user.username}")
        next_url = request.POST.get("next") or reverse_lazy("automation:task_assign_build_list")
        return redirect(next_url if next_url.startswith("/") else reverse_lazy("automation:task_assign_build_list"))


class AutomationTaskConfirmExecutableView(LoginRequiredMixin, StaffRequiredMixin, View):
    """验收通过：确认可执行"""

    def post(self, request, pk):
        task = get_object_or_404(
            AutomationTask,
            pk=pk,
            is_deleted=False,
            approval_status=AutomationTask.ApprovalStatus.ASSIGN_BUILD,
            build_status=AutomationTask.BuildStatus.COMPLETED,
        )
        task.approval_status = AutomationTask.ApprovalStatus.EXECUTABLE
        task.build_status = ""
        task.save(update_fields=["approval_status", "build_status", "updated_at"])
        _log_audit(request, "approve", "automation_task", task.pk, str(task), extra={"action": "confirm_executable"})
        messages.success(request, "已确认可执行")
        next_url = request.POST.get("next") or reverse_lazy("automation:task_build_acceptance_list")
        return redirect(next_url if next_url.startswith("/") else reverse_lazy("automation:task_build_acceptance_list"))


class AutomationTaskReturnRevisionView(LoginRequiredMixin, StaffRequiredMixin, View):
    """验收退回：退回再修改（从验收页操作）"""

    def post(self, request, pk):
        task = get_object_or_404(
            AutomationTask,
            pk=pk,
            is_deleted=False,
            approval_status=AutomationTask.ApprovalStatus.ASSIGN_BUILD,
        )
        task.build_status = AutomationTask.BuildStatus.RETURN_REVISION
        task.save(update_fields=["build_status", "updated_at"])
        _log_audit(request, "update", "automation_task", task.pk, str(task), extra={"build_status": "return_revision"})
        messages.success(request, "已退回再修改")
        next_url = request.POST.get("next") or reverse_lazy("automation:task_build_acceptance_list")
        return redirect(next_url if next_url.startswith("/") else reverse_lazy("automation:task_build_acceptance_list"))


class AutomationTaskDeletedListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """已删除任务"""
    model = AutomationTask
    template_name = "automation/task_deleted.html"
    context_object_name = "tasks"
    paginate_by = 20

    def get_queryset(self):
        return AutomationTask.objects.filter(is_deleted=True).select_related(
            "organization", "created_by", "deleted_by"
        ).order_by("-deleted_at")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return ctx


class AutomationTaskRestoreView(LoginRequiredMixin, StaffRequiredMixin, View):
    """恢复已删除任务"""
    success_url = reverse_lazy("automation:task_deleted_list")

    def post(self, request, pk):
        task = get_object_or_404(AutomationTask, pk=pk, is_deleted=True)
        task.is_deleted = False
        task.deleted_at = None
        task.deleted_by = None
        task.save(update_fields=["is_deleted", "deleted_at", "deleted_by", "updated_at"])
        _log_audit(request, "restore", "automation_task", task.pk, str(task))
        messages.success(request, "任务已恢复")
        return redirect(self.success_url)


def _approve_reject_redirect(request, default_url):
    """从 next 参数获取重定向 URL，支持返回任务看板"""
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and next_url.startswith("/"):
        return next_url
    return default_url


class AutomationTaskApproveView(LoginRequiredMixin, StaffRequiredMixin, View):
    """审批通过"""
    def post(self, request, pk):
        task = get_object_or_404(
            AutomationTask,
            pk=pk,
            is_deleted=False,
            approval_status=AutomationTask.ApprovalStatus.PENDING,
        )
        task.approval_status = AutomationTask.ApprovalStatus.APPROVED
        task.approved_at = timezone.now()
        task.approved_by = request.user
        task.save(update_fields=["approval_status", "approved_at", "approved_by", "updated_at"])
        _log_audit(request, "approve", "automation_task", task.pk, str(task))
        messages.success(request, "任务已审批通过")
        return redirect(_approve_reject_redirect(request, reverse_lazy("automation:task_pending_list")))


class AutomationTaskExecuteView(LoginRequiredMixin, StaffRequiredMixin, View):
    """执行任务 - 仅审批状态为「任务可执行」的任务可执行"""
    def post(self, request, pk):
        task = get_object_or_404(AutomationTask, pk=pk, is_deleted=False)
        if task.approval_status != AutomationTask.ApprovalStatus.EXECUTABLE:
            messages.error(request, "只有审批状态为「任务可执行」的任务才能执行")
            next_url = request.POST.get("next") or request.GET.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect(reverse_lazy("automation:task_list"))
        task.last_run_at = timezone.now()
        task.save(update_fields=["last_run_at", "updated_at"])
        _log_audit(request, "execute", "automation_task", task.pk, str(task))
        messages.success(request, f"任务「{task.name}」已记录执行")
        next_url = request.POST.get("next") or request.GET.get("next")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return redirect(reverse_lazy("automation:task_list"))


class AutomationTaskRejectView(LoginRequiredMixin, StaffRequiredMixin, View):
    """审批驳回"""
    def post(self, request, pk):
        task = get_object_or_404(
            AutomationTask,
            pk=pk,
            is_deleted=False,
            approval_status=AutomationTask.ApprovalStatus.PENDING,
        )
        task.approval_status = AutomationTask.ApprovalStatus.REJECTED
        task.approved_at = timezone.now()
        task.approved_by = request.user
        task.save(update_fields=["approval_status", "approved_at", "approved_by", "updated_at"])
        _log_audit(request, "reject", "automation_task", task.pk, str(task))
        messages.success(request, "任务已驳回")
        return redirect(_approve_reject_redirect(request, reverse_lazy("automation:task_pending_list")))


class AutomationTaskCancelView(LoginRequiredMixin, StaffRequiredMixin, View):
    """审批取消 - 将待审核任务设为被取消"""
    def post(self, request, pk):
        task = get_object_or_404(
            AutomationTask,
            pk=pk,
            is_deleted=False,
            approval_status=AutomationTask.ApprovalStatus.PENDING,
        )
        task.approval_status = AutomationTask.ApprovalStatus.CANCELLED
        task.approved_at = timezone.now()
        task.approved_by = request.user
        task.save(update_fields=["approval_status", "approved_at", "approved_by", "updated_at"])
        _log_audit(request, "cancel", "automation_task", task.pk, str(task))
        messages.success(request, "任务已取消")
        return redirect(_approve_reject_redirect(request, reverse_lazy("automation:task_pending_list")))


APPROVAL_STATUS_MAP = {
    "pending": ("待审核", "warning"),
    "approved": ("审批通过", "success"),
    "assign_build": ("指派人员构建工作", "info"),
    "assign_done": ("指派任务完成", "primary"),
    "executable": ("任务可执行", "success"),
    "rejected": ("已驳回", "danger"),
    "cancelled": ("被取消", "secondary"),
}

AUDIT_ACTION_MAP = {
    "approved": "approve",
    "assign_build": "update",
    "assign_done": "update",
    "executable": "update",
    "rejected": "reject",
    "cancelled": "cancel",
    "pending": "update",
}


class AutomationTaskSetApprovalStatusView(LoginRequiredMixin, StaffRequiredMixin, View):
    """设置审批状态 API - 支持任意状态间切换，无刷新"""
    def post(self, request, pk):
        task = get_object_or_404(AutomationTask, pk=pk, is_deleted=False)
        status = (request.POST.get("status") or request.GET.get("status") or "").strip().lower()
        if status not in APPROVAL_STATUS_MAP:
            return JsonResponse({"ok": False, "error": "无效状态"}, status=400)
        task.approval_status = status
        task.approved_at = timezone.now()
        task.approved_by = request.user
        task.save(update_fields=["approval_status", "approved_at", "approved_by", "updated_at"])
        action = AUDIT_ACTION_MAP.get(status, "update")
        _log_audit(request, action, "automation_task", task.pk, str(task), extra={"approval_status": status})
        label, badge = APPROVAL_STATUS_MAP[status]
        return JsonResponse({"ok": True, "status": status, "label": label, "badge": badge})


class AutomationTaskPreviewView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    """任务预览 - 只读展示，管理员/高级管理员可添加备注"""
    model = AutomationTask
    template_name = "automation/task_preview.html"
    context_object_name = "task"

    def get_queryset(self):
        return AutomationTask.objects.filter(is_deleted=False).select_related(
            "organization", "created_by", "approved_by", "assigned_to"
        ).prefetch_related("attachments", "remarks")

    def get_context_data(self, **kwargs):
        import json
        ctx = super().get_context_data(**kwargs)
        ctx["remarks"] = self.object.remarks.select_related("user").order_by("-created_at")
        ctx["can_add_remark"] = self.request.user.is_staff or self.request.user.is_superuser
        ctx["config_display"] = json.dumps(self.object.config or {}, ensure_ascii=False, indent=2)
        return ctx

    def post(self, request, pk):
        task = get_object_or_404(AutomationTask, pk=pk, is_deleted=False)
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, "仅管理员和高级管理员可添加备注")
            return redirect("automation:task_preview", pk=pk)
        content = (request.POST.get("remark_content") or "").strip()
        if not content:
            messages.warning(request, "请输入备注内容")
            return redirect("automation:task_preview", pk=pk)
        TaskRemark.objects.create(task=task, user=request.user, content=content)
        messages.success(request, "备注已添加")
        return redirect("automation:task_preview", pk=pk)


class AutomationTaskExecutionHistoryView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    """任务执行详情 - 展示创建、修改、执行等完整审计轨迹"""
    model = AutomationTask
    template_name = "automation/task_execution_history.html"
    context_object_name = "task"

    def get_queryset(self):
        return AutomationTask.objects.filter(is_deleted=False)

    def get_context_data(self, **kwargs):
        from apps.audit.models import AuditLog

        ctx = super().get_context_data(**kwargs)
        # 该任务的所有审计记录（创建、修改、执行、审批等）按时间倒序
        ctx["audit_logs"] = AuditLog.objects.filter(
            target_model="automation_task", target_id=self.object.pk
        ).select_related("user").order_by("-created_at")
        return ctx


class AutomationTaskPermanentDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, DeleteView):
    """永久删除（仅超级管理员）"""
    model = AutomationTask
    template_name = "automation/task_confirm_permanent_delete.html"
    context_object_name = "task"
    success_url = reverse_lazy("automation:task_deleted_list")

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        pk, repr_str = self.object.pk, str(self.object)
        super().delete(request, *args, **kwargs)
        _log_audit(request, "permanent_delete", "automation_task", pk, repr_str)
        messages.success(request, "任务已永久删除")
        return redirect(self.success_url)
