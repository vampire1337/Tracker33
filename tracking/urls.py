from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from django.views.generic import RedirectView, TemplateView
from .views import (
    ApplicationViewSet,
    UserActivityViewSet,
    KeyboardActivityViewSet,
    StatisticsView,
    DashboardView,
    LogsView,
    TrackedApplicationViewSet,
    TimeLogListCreateView,
    TimeLogDetailView,
    TimeLogListView,
    TimeLogCreateView,
    TimeLogUpdateView,
    TimeLogDeleteView,
    LandingView,
    StatisticsAPIView,
    ExportStatisticsAPIView,
    DailyActivityAPIView,
    TimeDistributionAPIView,
    DashboardAPIView,
    toggle_productive,
    create_activity,
    list_applications,
    get_statistics,
    get_user_profile,
    generate_qr_token,
    authenticate_qr_token,
    qr_auth_status
)

# API router
api_router = DefaultRouter()
api_router.register(r'tracked-apps', TrackedApplicationViewSet, basename='tracked-app')
api_router.register(r'applications', ApplicationViewSet)
api_router.register(r'activities', UserActivityViewSet)
api_router.register(r'keyboard', KeyboardActivityViewSet)

# API endpoints
api_urlpatterns = [
    path('token/', obtain_auth_token, name='api_token_auth'),
    path('timelogs/', TimeLogListCreateView.as_view(), name='timelog-list-create'),
    path('timelogs/<int:pk>/', TimeLogDetailView.as_view(), name='timelog-detail'),
    path('statistics/', StatisticsAPIView.as_view(), name='statistics-api'),
    path('export-statistics/', ExportStatisticsAPIView.as_view(), name='export-statistics-api'),
    path('daily-activity/', DailyActivityAPIView.as_view(), name='daily-activity-api'),
    path('time-distribution/', TimeDistributionAPIView.as_view(), name='time-distribution-api'),
    path('dashboard/', DashboardAPIView.as_view(), name='dashboard-api'),
    path('toggle-productive/', toggle_productive, name='toggle-productive-api'),
    path('activities/', create_activity, name='api_create_activity'),
    path('applications/', list_applications, name='api_list_applications'),
    path('user-profile/', get_user_profile, name='api_user_profile'),
    path('qr/generate/', generate_qr_token, name='api_qr_generate'),
    path('qr/authenticate/', authenticate_qr_token, name='api_qr_authenticate'),
    path('qr/status/', qr_auth_status, name='api_qr_status'),
]

# Web interface
web_urlpatterns = [
    path('', LandingView.as_view(), name='landing'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('statistics/', StatisticsView.as_view(), name='statistics'),
    path('logs/', LogsView.as_view(), name='logs'),
    path('timelogs/', TimeLogListView.as_view(), name='timelog-list'),
    path('timelogs/create/', TimeLogCreateView.as_view(), name='timelog-create'),
    path('timelogs/<int:pk>/update/', TimeLogUpdateView.as_view(), name='timelog-update'),
    path('timelogs/<int:pk>/delete/', TimeLogDeleteView.as_view(), name='timelog-delete'),
    path('qr-connect/', TemplateView.as_view(template_name='qr_connect.html'), name='qr_connect'),
]

# Combine all URL patterns
urlpatterns = [
    # API URLs
    path('api/', include(api_router.urls)),
    path('api/', include(api_urlpatterns)),
    # Web URLs
    path('', include(web_urlpatterns)),
] 