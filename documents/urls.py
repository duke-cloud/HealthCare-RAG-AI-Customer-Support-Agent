from django.urls import path
from . import views
urlpatterns = [
    path('',           views.doc_list,   name='doc_list'),
    path('add/',       views.doc_add,    name='doc_add'),
    path('reindex/',   views.reindex_all,name='reindex'),
    path('<int:pk>/delete/', views.doc_delete, name='doc_delete'),
]
