from django.urls import path

from . import views

urlpatterns = [
    path("public_keys/", views.PublicKeyList.as_view()),
]
