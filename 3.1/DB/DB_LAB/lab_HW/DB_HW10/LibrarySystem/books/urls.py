from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    path('', views.book_list, name='book_list'),
    path('create/', views.book_create, name='book_create'),
    path('edit/<str:pk>/', views.book_update, name='book_update'),
    path('delete/<str:pk>/', views.book_delete, name='book_delete'),
]