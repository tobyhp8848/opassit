"""组织管理视图 - AdminLTE 风格"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

from .models import Organization


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect("/")


class OrganizationListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = Organization
    template_name = "organizations/organization_list.html"
    context_object_name = "organizations"
    paginate_by = 20

    def get_queryset(self):
        qs = Organization.objects.select_related("parent").order_by("parent__name", "name")
        org_type = self.request.GET.get("org_type")
        if org_type:
            qs = qs.filter(org_type=org_type)
        is_active = self.request.GET.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active == "1")
        search = self.request.GET.get("q", "").strip()
        if search:
            qs = qs.filter(name__icontains=search) | qs.filter(code__icontains=search)
        return qs.distinct()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["org_type_filter"] = self.request.GET.get("org_type", "")
        ctx["is_active_filter"] = self.request.GET.get("is_active", "")
        ctx["search_q"] = self.request.GET.get("q", "")
        ctx["org_type_choices"] = Organization.OrgType.choices
        return ctx


class OrganizationFormMixin:
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = Organization.objects.order_by("org_type", "name")
        obj = getattr(self, "object", None)
        if obj:
            qs = qs.exclude(pk=obj.pk)  # 不能选自己为上级
        ctx["parent_options"] = qs
        return ctx


class OrganizationCreateView(OrganizationFormMixin, LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Organization
    template_name = "organizations/organization_form.html"
    fields = ["name", "code", "org_type", "parent", "description", "is_active"]
    success_url = reverse_lazy("organizations:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["org"] = None
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "组织创建成功")
        return super().form_valid(form)


class OrganizationUpdateView(OrganizationFormMixin, LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = Organization
    template_name = "organizations/organization_form.html"
    fields = ["name", "code", "org_type", "parent", "description", "is_active"]
    context_object_name = "org"
    success_url = reverse_lazy("organizations:list")

    def form_valid(self, form):
        messages.success(self.request, "组织已更新")
        return super().form_valid(form)


class OrganizationDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Organization
    template_name = "organizations/organization_confirm_delete.html"
    context_object_name = "org"
    success_url = reverse_lazy("organizations:list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "组织已删除")
        return super().delete(request, *args, **kwargs)
