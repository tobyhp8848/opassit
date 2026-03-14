from django.urls import path
from . import views

app_name = "automation"

urlpatterns = [
    path("", views.AutomationTaskListView.as_view(), name="task_list"),
    path("batch/", views.AutomationTaskBatchActionView.as_view(), name="task_batch"),
    path("board/", views.AutomationTaskBoardView.as_view(), name="task_board"),
    path("add/", views.AutomationTaskCreateView.as_view(), name="task_add"),
    path("pending/", views.AutomationTaskPendingListView.as_view(), name="task_pending_list"),
    path("assign-build/", views.AutomationTaskAssignBuildListView.as_view(), name="task_assign_build_list"),
    path("build-acceptance/", views.AutomationTaskBuildAcceptanceListView.as_view(), name="task_build_acceptance_list"),
    path("executable/", views.AutomationTaskExecutableListView.as_view(), name="task_executable_list"),
    path("<int:pk>/set-build-status/", views.AutomationTaskSetBuildStatusView.as_view(), name="task_set_build_status"),
    path("<int:pk>/assign-user/", views.AutomationTaskAssignUserView.as_view(), name="task_assign_user"),
    path("batch-assign/", views.AutomationTaskBatchAssignView.as_view(), name="task_batch_assign"),
    path("<int:pk>/confirm-executable/", views.AutomationTaskConfirmExecutableView.as_view(), name="task_confirm_executable"),
    path("<int:pk>/return-revision/", views.AutomationTaskReturnRevisionView.as_view(), name="task_return_revision"),
    path("deleted/", views.AutomationTaskDeletedListView.as_view(), name="task_deleted_list"),
    path("<int:pk>/", views.AutomationTaskUpdateView.as_view(), name="task_edit"),
    path("<int:pk>/preview/", views.AutomationTaskPreviewView.as_view(), name="task_preview"),
    path("<int:pk>/delete/", views.AutomationTaskDeleteView.as_view(), name="task_delete"),
    path("<int:pk>/restore/", views.AutomationTaskRestoreView.as_view(), name="task_restore"),
    path("<int:pk>/approve/", views.AutomationTaskApproveView.as_view(), name="task_approve"),
    path("<int:pk>/reject/", views.AutomationTaskRejectView.as_view(), name="task_reject"),
    path("<int:pk>/cancel/", views.AutomationTaskCancelView.as_view(), name="task_cancel"),
    path("<int:pk>/set-approval-status/", views.AutomationTaskSetApprovalStatusView.as_view(), name="task_set_approval_status"),
    path("<int:pk>/execute/", views.AutomationTaskExecuteView.as_view(), name="task_execute"),
    path("<int:pk>/execution-history/", views.AutomationTaskExecutionHistoryView.as_view(), name="task_execution_history"),
    path("<int:pk>/permanent-delete/", views.AutomationTaskPermanentDeleteView.as_view(), name="task_permanent_delete"),
]
