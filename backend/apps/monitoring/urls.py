from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_page),
    path('dashboard/', views.dashboard),
    path('datasets/', views.datasets_page),
    path('api/dashboard/', views.dashboard_api),
    path('api/sensors/', views.sensors_api),
    path('api/sensors/<str:sensor_id>/history/', views.sensor_history),
    path('api/pipeline/', views.pipeline),
    path('api/model/', views.model_api),
    path('api/upload/', views.upload_api),
    path('api/iot/telemetry/', views.iot_telemetry_api),
    path('api/report/', views.api_report),
    path('api/reports/', views.reports_api),
    path('api/reports/generate/', views.generate_report),
    path('api/file_content/', views.api_file_content),
    path('api/save_case/', views.api_save_case),
    path('api/profile/', views.api_profile),
    path('reports/<str:name>/', views.report_file),
    *[path(f'api/{k}/', views.derived, {'kind': k}) for k in ['predictions', 'risk', 'optimization', 'alerts']],
    *[path(f'api/simulation/{a}/', views.simulation, {'action': a}) for a in ['start', 'pause', 'reset']],
    path('api/alerts/<str:alert_id>/resolve/', views.resolve_alert),
    *[path(f'{name}/', views.page, {'name': name.replace('-', ' ').title()}) for name in [
        'live-monitoring', 'predictions', 'optimization', 'alerts', 'model', 'sensors', 'reports', 'upload', 'methodology'
    ]]
]
