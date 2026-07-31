from django.urls import path
from case_platform import views

urlpatterns = [
    path('case_main/', views.test_case_view, name='test_case_view'),
    path('ai_complete/', views.ai_complete_view, name='ai_complete_view'),
    path('batch_import/', views.batch_import_view, name='batch_import_view'),
    path('generate_test_case/', views.generate_test_case, name='generate_test_case'),

    path('create', views.create_test_case, name='create_test_case'),
    path('delete', views.delete_test_case, name='delete_test_case'),
    path('update', views.update_test_case, name='update_test_case'),
    path('get', views.get_test_case, name='get_test_case'),
]
