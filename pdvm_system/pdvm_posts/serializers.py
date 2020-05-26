from rest_framework import serializers
from .models import pdvm_posts, pdvm_comments   #import model

# Create a class
class postsSerializer(serializers.ModelSerializer):

    class Meta:
        model = pdvm_posts
        fields = '__all__'
        
class commentSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = pdvm_comments
        fields = '__all__'