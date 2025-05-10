from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.AdminDashboardView.as_view(), name='dashboard'),
    path('users/', views.UserListView.as_view(), name='users'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
    path('applications/', views.ApplicationListView.as_view(), name='applications'),
    path('activities/', views.ActivityListView.as_view(), name='activities'),
    path('logs/', views.LogsView.as_view(), name='logs'),
    path('database/', views.DatabaseTablesView.as_view(), name='database'),
] 