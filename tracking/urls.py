from django.urls import path, include
from django.views.generic import RedirectView, TemplateView
from .views import (
    StatisticsView,
    DashboardView,
    LogsView,
    TimeLogListView,
    TimeLogCreateView,
    TimeLogUpdateView,
    TimeLogDeleteView,
    LandingView,
)

# Только веб-интерфейс, никаких API!
urlpatterns = [
    path('', LandingView.as_view(), name='landing'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('statistics/', StatisticsView.as_view(), name='statistics'),
    path('logs/', LogsView.as_view(), name='logs'),
    path('timelogs/', TimeLogListView.as_view(), name='timelog-list'),
    path('timelogs/create/', TimeLogCreateView.as_view(), name='timelog-create'),
    path('timelogs/<int:pk>/update/', TimeLogUpdateView.as_view(), name='timelog-update'),
    path('timelogs/<int:pk>/delete/', TimeLogDeleteView.as_view(), name='timelog-delete'),
] 