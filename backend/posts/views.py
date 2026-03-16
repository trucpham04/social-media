from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Post
from .serializers import PostSerializer, PostListSerializer
from .utils import delete_file_from_s3


class PostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Post CRUD operations.
    Requires authentication for all operations.
    """

    permission_classes = [IsAuthenticated]
    queryset = Post.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return PostListSerializer
        return PostSerializer

    def get_queryset(self):
        """Filter posts based on visibility and user"""
        user = self.request.user
        queryset = Post.objects.select_related("user").all()

        # Filter by visibility
        visibility = self.request.query_params.get("visibility", None)
        if visibility:
            queryset = queryset.filter(visibility=visibility)

        # Filter by user
        user_id = self.request.query_params.get("user_id", None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # Filter posts user can see
        # Public posts are visible to everyone
        # Friends posts are visible to friends (simplified: visible to everyone for now, can be enhanced later)
        # Private posts are only visible to the owner
        if self.action == "list":
            queryset = queryset.filter(
                Q(visibility=Post.VISIBILITY_PUBLIC)
                | Q(visibility=Post.VISIBILITY_FRIENDS)  # Friends posts visible to all for now
                | Q(visibility=Post.VISIBILITY_PRIVATE, user=user)  # Private posts only to owner
            )

        return queryset

    def perform_create(self, serializer):
        """Set the user to the authenticated user"""
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        """Delete post and its media from S3"""
        instance = self.get_object()

        # Check if user owns the post
        if instance.user != request.user:
            return Response(
                {"detail": "You do not have permission to delete this post."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Delete media from S3 if it exists
        if instance.media_url:
            delete_file_from_s3(instance.media_url)

        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Update post - only owner can update"""
        instance = self.get_object()

        # Check if user owns the post
        if instance.user != request.user:
            return Response(
                {"detail": "You do not have permission to update this post."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """Partial update post - only owner can update"""
        instance = self.get_object()

        # Check if user owns the post
        if instance.user != request.user:
            return Response(
                {"detail": "You do not have permission to update this post."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def my_posts(self, request):
        """Get all posts by the authenticated user"""
        posts = self.get_queryset().filter(user=request.user)
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)
