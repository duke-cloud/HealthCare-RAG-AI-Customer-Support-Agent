from django.urls import path
from . import views
urlpatterns = [
    path('',                         views.chat_home,      name='chat'),
    path('session/<int:pk>/',        views.chat_session,   name='chat_session'),
    path('session/new/',             views.new_session,    name='new_session'),
    path('session/<int:pk>/ask/',    views.ask,            name='ask'),
    path('message/<int:msg_id>/feedback/', views.feedback, name='feedback'),
    path('ticket/create/',           views.create_ticket,  name='create_ticket'),
    path('ticket/my/',               views.my_tickets,     name='my_tickets'),
]
