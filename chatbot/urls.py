from django.urls import path
from . import views

urlpatterns = [
    path('', views.chatbot_page, name='chatbot_page'),
    path('clear/', views.clear_chat, name='clear_chat'),
]