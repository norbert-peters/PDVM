from django.contrib import admin
from .models import pdvm_posts, pdvm_comments

# Register your models here.
admin.site.register(pdvm_posts)
admin.site.register(pdvm_comments)
