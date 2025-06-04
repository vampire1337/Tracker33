from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    ApplicationViewSet,
    UserActivityViewSet,
    KeyboardActivityViewSet,
    TrackedApplicationViewSet,
    TimeLogListCreateView,
    TimeLogDetailView,
    StatisticsAPIView,
    ExportStatisticsAPIView,
    DailyActivityAPIView,
    TimeDistributionAPIView,
    DashboardAPIView,
    toggle_productive,
    create_activity,
    list_applications,
    get_user_profile
)

# API router
api_router = DefaultRouter()
api_router.register(r'tracked-apps', TrackedApplicationViewSet, basename='tracked-app')
api_router.register(r'applications', ApplicationViewSet)
api_router.register(r'activities', UserActivityViewSet)
api_router.register(r'keyboard', KeyboardActivityViewSet)

# API endpoints
urlpatterns = [
    # DRF router URLs
    path('', include(api_router.urls)),
    
    # Auth endpoints
    path('token/', obtain_auth_token, name='api_token_auth'),
    path('auth/token/', obtain_auth_token, name='api_auth_token'),
    
    # Custom API endpoints
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
] 