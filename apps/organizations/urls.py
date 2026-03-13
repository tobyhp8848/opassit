from django.urls import path
from . import views

app_name = "organizations"

urlpatterns = [
    path("", views.OrganizationListView.as_view(), name="list"),
    path("add/", views.OrganizationCreateView.as_view(), name="add"),
    path("<int:pk>/", views.OrganizationUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.OrganizationDeleteView.as_view(), name="delete"),
]
