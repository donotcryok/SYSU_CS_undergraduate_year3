from django.contrib import admin
from django.urls import path
from books import views # 导入我们的views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 首页
    path('', views.index, name='index'),
    
    # 图书功能
    path('books/', views.book_list, name='book_list'),
    path('books/add/', views.book_create, name='book_create'),
    path('books/edit/<str:pk>/', views.book_update, name='book_update'), # <str:pk> 用来接收图书ID
    path('books/delete/<str:pk>/', views.book_delete, name='book_delete'),
]