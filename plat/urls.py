from django.urls import path

from plat.views import test_view

urlpatterns = [
    path('test', test_view),
]
