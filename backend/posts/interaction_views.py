from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

from .models import PostReport, Like, Comment, Post
from .interaction_serializers import (
    PostReportSerializer,
    PostReportUpdateSerializer,
    LikeSerializer,
    CommentSerializer,
    CommentListSerializer,
)


class PostReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Post Report operations.
    Users can create reports, admins can review them.
    """

    permission_classes = [IsAuthenticated]
    queryset = PostReport.objects.select_related("reporter", "post", "reviewed_by").all()

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return PostReportUpdateSerializer
        return PostReportSerializer

    def get_queryset(self):
        """Filter reports based on user role"""
        user = self.request.user

        # Admins can see all reports
        if user.is_staff or getattr(user, "role", None) == "admin":
            return self.queryset

        # Regular users can only see their own reports
        return self.queryset.filter(reporter=user)

    def perform_create(self, serializer):
        """Set reporter to authenticated user"""
        serializer.save()

    def update(self, request, *args, **kwargs):
        """Only admins can update report status"""
        if not (request.user.is_staff or getattr(request.user, "role", None) == "admin"):
            return Response(
                {"detail": "Only admins can review reports."},
                status=status.HTTP_403_FORBIDDEN,
            )

        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            # Set reviewed_by and reviewed_at
            serializer.save(
                reviewed_by=request.user, reviewed_at=timezone.now()
            )
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        """Only admins can partially update report status"""
        return self.update(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def pending(self, request):
        """Get all pending reports (admin only)"""
        if not (request.user.is_staff or getattr(request.user, "role", None) == "admin"):
            return Response(
                {"detail": "Only admins can view pending reports."},
                status=status.HTTP_403_FORBIDDEN,
            )

        pending_reports = self.queryset.filter(
            review_status=PostReport.REVIEW_STATUS_PENDING
        )
        serializer = self.get_serializer(pending_reports, many=True)
        return Response(serializer.data)


class LikeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Like operations.
    Users can like/unlike posts with different reactions.
    """

    permission_classes = [IsAuthenticated]
    queryset = Like.objects.select_related("user", "post").all()
    serializer_class = LikeSerializer

    def get_queryset(self):
        """Filter likes"""
        queryset = self.queryset

        # Filter by post
        post_id = self.request.query_params.get("post_id", None)
        if post_id:
            queryset = queryset.filter(post_id=post_id)

        # Filter by user
        user_id = self.request.query_params.get("user_id", None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        return queryset

    def perform_create(self, serializer):
        """Set user to authenticated user"""
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        """Unlike a post"""
        instance = self.get_object()

        # Check if user owns the like
        if instance.user != request.user:
            return Response(
                {"detail": "You can only remove your own likes."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=["post"])
    def toggle(self, request):
        """Toggle like on a post (like if not liked, unlike if liked)"""
        post_id = request.data.get("post_id")
        reaction = request.data.get("reaction", Like.REACTION_LIKE)

        if not post_id:
            return Response(
                {"detail": "post_id is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        post = get_object_or_404(Post, id=post_id)
        like = Like.objects.filter(user=request.user, post=post).first()

        if like:
            # Unlike
            like.delete()
            return Response({"liked": False, "message": "Post unliked"})
        else:
            # Like
            like = Like.objects.create(user=request.user, post=post, reaction=reaction)
            serializer = self.get_serializer(like)
            return Response({"liked": True, **serializer.data})


class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Comment operations.
    Users can create, read, update, and delete their own comments.
    """

    permission_classes = [IsAuthenticated]
    queryset = Comment.objects.select_related("user", "post").all()

    def get_serializer_class(self):
        if self.action == "list":
            return CommentListSerializer
        return CommentSerializer

    def get_queryset(self):
        """Filter comments"""
        queryset = self.queryset

        # Filter by post
        post_id = self.request.query_params.get("post_id", None)
        if post_id:
            queryset = queryset.filter(post_id=post_id)

        # Filter by user
        user_id = self.request.query_params.get("user_id", None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        return queryset

    def perform_create(self, serializer):
        """Set user to authenticated user"""
        serializer.save()

    def update(self, request, *args, **kwargs):
        """Update comment - only owner can update"""
        instance = self.get_object()

        if instance.user != request.user:
            return Response(
                {"detail": "You can only update your own comments."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """Partial update - only owner can update"""
        instance = self.get_object()

        if instance.user != request.user:
            return Response(
                {"detail": "You can only update your own comments."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete comment - only owner can delete"""
        instance = self.get_object()

        if instance.user != request.user:
            return Response(
                {"detail": "You can only delete your own comments."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().destroy(request, *args, **kwargs)
