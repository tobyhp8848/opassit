from django.urls import path
from . import views

app_name = "automation"

urlpatterns = [
    path("", views.AutomationTaskListView.as_view(), name="task_list"),
    path("add/", views.AutomationTaskCreateView.as_view(), name="task_add"),
    path("<int:pk>/", views.AutomationTaskUpdateView.as_view(), name="task_edit"),
    path("<int:pk>/delete/", views.AutomationTaskDeleteView.as_view(), name="task_delete"),
]
