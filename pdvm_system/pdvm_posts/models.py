from django.db import models
from pdvm_base.pdvm_util import getNewId

# Create your models here.

# Entry some data into model
class pdvm_posts(models.Model):
    userId = models.CharField(max_length=10, )
    id = models.UUIDField(primary_key=True, default=getNewId ,unique=True)
    title = models.CharField(max_length=100)
    body = models.TextField()

# Create a string representation
    def __str__(self):
        return self.title
    
class pdvm_comments(models.Model):
    postId = models.UUIDField()
    id = models.UUIDField(primary_key=True, default=getNewId ,unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254)
    body = models.TextField()

# Create a string representation
    def __str__(self):
        return self.name + self.email
