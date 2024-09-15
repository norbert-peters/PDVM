from django.urls import path
from . import views

urlpatterns = [
    path('', views.postlist.as_view()),
    path('comments', views.commentlist.as_view()),
#    path('<int:pk>/', views.DetailTodo.as_view()),
#    path('', views.ListTodo.as_view()),
#    path('<int:pk>/', views.DetailTodo.as_view()),
]

