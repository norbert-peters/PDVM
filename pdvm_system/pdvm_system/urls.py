"""pdvm_system URL Configuration

"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls import url
from pdvm_posts import views        #import views

urlpatterns = [
    path('admin/', admin.site.urls),
#    path('api/posts/', include('pdvm_posts.urls')),
#    path('api/posts/comments/', views.commentlist.as_view()),
    url(r'^api/posts/$', views.postlist),
    url(r'^api/posts/(?P<pk>[-a-zA-Z0-9_]+)$', views.postdetail),
    url(r'^api/comments/$', views.commentlist),
    url(r'^api/comments/(?P<pk>[-a-zA-Z0-9_]+)$', views.commentdetail),
    url(r'^api/postcomments/(?P<pk>[-a-zA-Z0-9_]+)/$', views.postcomment),
]
 