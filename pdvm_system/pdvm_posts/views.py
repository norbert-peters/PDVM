"""from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import pdvm_posts, pdvm_comments 
from .serializers import postsSerializer, commentSerializer


class postlist(APIView):

    def get(self,request):
        data = pdvm_posts.objects.all()
        serializer = postsSerializer(data, many= True)
        return Response(serializer.data) # Return JSON

    def post(self):
        pass
    
class commentlist(APIView):
    
    def get(self,request):
        data = pdvm_comments.objects.all()
        seralizer = commentSerializer(data, many = True)
        return Response(seralizer.data) # Return JSON
    
    def psst(self):
        pass
    
    
# todos/views.py
#from rest_framework import generics
#
#from .models import Todo
#from .serializers import TodoSerializer
#
#
#class ListTodo(generics.ListCreateAPIView):
#    queryset = Todo.objects.all()
#    serializer_class = TodoSerializer
#
#
#class DetailTodo(generics.RetrieveUpdateDestroyAPIView):
#    queryset = Todo.objects.all()
#    serializer_class = TodoSerializer
"""
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import pdvm_posts, pdvm_comments 
from .serializers import postsSerializer, commentSerializer


@api_view(['GET', 'POST'])
def postlist(request):
    """
 List  posts, or create a new post.
 """
    if request.method == 'GET':
        data = []
        nextPage = 1
        previousPage = 1
        posts = pdvm_posts.objects.all()
        page = request.GET.get('page', 1)
        paginator = Paginator(posts, 5)
        try:
            data = paginator.page(page)
        except PageNotAnInteger:
            data = paginator.page(1)
        except EmptyPage:
            data = paginator.page(paginator.num_pages)

        serializer = postsSerializer(data,context={'request': request} ,many=True)
        if data.has_next():
            nextPage = data.next_page_number()
        if data.has_previous():
            previousPage = data.previous_page_number()

        return Response({'data': serializer.data , 'count': paginator.count, 'numpages' : paginator.num_pages, 'nextlink': '/api/posts/?page=' + str(nextPage), 'prevlink': '/api/posts/?page=' + str(previousPage)})

    elif request.method == 'POST':
        serializer = postsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def postdetail(request, pk):
    """
 Retrieve, update or delete a post by id/pk.
 """
    try:
        post = pdvm_posts.objects.get(pk=pk)
    except pdvm_posts.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = postsSerializer(post,context={'request': request})
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = postsSerializer(post, data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
@api_view(['GET', 'POST'])
def commentlist(request):
    """
 List  comments, or create a new comment.
 """
    if request.method == 'GET':
        data = []
        nextPage = 1
        previousPage = 1
        comments = pdvm_comments.objects.all()
        page = request.GET.get('page', 1)
        paginator = Paginator(comments, 5)
        try:
            data = paginator.page(page)
        except PageNotAnInteger:
            data = paginator.page(1)
        except EmptyPage:
            data = paginator.page(paginator.num_pages)

        serializer = commentSerializer(data,context={'request': request} ,many=True)
        if data.has_next():
            nextPage = data.next_page_number()
        if data.has_previous():
            previousPage = data.previous_page_number()

        return Response({'data': serializer.data , 'count': paginator.count, 'numpages' : paginator.num_pages, 'nextlink': '/api/comments/?page=' + str(nextPage), 'prevlink': '/api/comments/?page=' + str(previousPage)})

    elif request.method == 'POST':
        serializer = commentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def postcomment(request, pk):
    print("request "+ str(request.data))
    """
 List  comments for post.
 """
    if request.method == 'GET':
        data = []
        nextPage = 1
        previousPage = 1
        comments = pdvm_comments.objects.all().filter(postId=pk)
        page = request.GET.get('page', 1)
        paginator = Paginator(comments, 5)  
        try:
            data = paginator.page(page)
        except PageNotAnInteger:
            data = paginator.page(1)
        except EmptyPage:
            data = paginator.page(paginator.num_pages)

        serializer = commentSerializer(data,context={'request': request} ,many=True)
        if data.has_next():
            nextPage = data.next_page_number()
        if data.has_previous():
            previousPage = data.previous_page_number()

        return Response({'data': serializer.data , 'count': paginator.count, 'numpages' : paginator.num_pages, 'nextlink': '/api/postcomments/?page=' + str(nextPage), 'prevlink': '/api/postcomments/?page=' + str(previousPage)})

@api_view(['GET', 'PUT', 'DELETE'])
def commentdetail(request, pk):
    """
 Retrieve, update or delete a comment by id/pk.
 """
    try:
        comment = pdvm_comments.objects.get(pk=pk)
    except pdvm_comments.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = commentSerializer(comment, context={'request': request})
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = commentSerializer(comment, data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    