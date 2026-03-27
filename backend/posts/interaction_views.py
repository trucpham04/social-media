from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)

from .models import PostReport, Like, Comment, Post
from .interaction_serializers import (
    PostReportSerializer,
    PostReportUpdateSerializer,
    LikeSerializer,
    CommentSerializer,
    CommentListSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="Danh sách báo cáo bài viết",
        description="User thường chỉ xem được báo cáo của mình. Admin xem được tất cả.",
        tags=["posts"],
    ),
    create=extend_schema(
        summary="Tạo báo cáo bài viết",
        description="Tạo báo cáo cho một bài viết.",
        examples=[
            OpenApiExample(
                "Mẫu báo cáo bài viết",
                value={"post": 1, "reason": "Nội dung vi phạm tiêu chuẩn cộng đồng"},
                request_only=True,
            )
        ],
        tags=["posts"],
    ),
    retrieve=extend_schema(
        summary="Chi tiết báo cáo",
        description="Lấy thông tin chi tiết của một báo cáo.",
        tags=["posts"],
    ),
    update=extend_schema(
        summary="Duyệt báo cáo (Admin)",
        description="Admin cập nhật trạng thái: pending | approved | rejected.",
        examples=[
            OpenApiExample(
                "Mẫu duyệt báo cáo",
                value={"review_status": "approved"},
                request_only=True,
            )
        ],
        tags=["posts"],
    ),
    partial_update=extend_schema(
        summary="Cập nhật một phần báo cáo (Admin)",
        description="Admin cập nhật một phần trạng thái báo cáo.",
        examples=[
            OpenApiExample(
                "Mẫu từ chối báo cáo",
                value={"review_status": "rejected"},
                request_only=True,
            )
        ],
        tags=["posts"],
    ),
    destroy=extend_schema(
        summary="Xóa báo cáo",
        description="Xóa một báo cáo bài viết.",
        tags=["posts"],
    ),
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
    @extend_schema(
        summary="Danh sách báo cáo chờ duyệt",
        description="Admin lấy danh sách báo cáo có trạng thái pending.",
        tags=["posts"],
    )
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


@extend_schema_view(
    list=extend_schema(
        summary="Danh sách lượt reaction",
        description="Lấy danh sách likes/reactions theo bộ lọc.",
        parameters=[
            OpenApiParameter(
                name="post_id",
                description="Lọc theo bài viết",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="user_id",
                description="Lọc theo người dùng",
                required=False,
                type=int,
            ),
        ],
        tags=["posts"],
    ),
    create=extend_schema(
        summary="Thả reaction",
        description="Thả reaction cho bài viết. Nếu đã reaction thì cập nhật reaction.",
        examples=[
            OpenApiExample(
                "Mẫu thả tim",
                value={"post": 1, "reaction": "love"},
                request_only=True,
            )
        ],
        tags=["posts"],
    ),
    retrieve=extend_schema(
        summary="Chi tiết reaction",
        description="Lấy thông tin một reaction.",
        tags=["posts"],
    ),
    destroy=extend_schema(
        summary="Bỏ reaction",
        description="Xóa reaction của chính người dùng.",
        tags=["posts"],
    ),
)
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
    @extend_schema(
        summary="Toggle reaction",
        description="Nếu đã reaction thì bỏ, nếu chưa thì tạo mới.",
        examples=[
            OpenApiExample(
                "Mẫu toggle reaction",
                value={"post_id": 1, "reaction": "haha"},
                request_only=True,
            )
        ],
        tags=["posts"],
    )
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


@extend_schema_view(
    list=extend_schema(
        summary="Danh sách bình luận",
        description="Lấy danh sách bình luận theo bộ lọc.",
        parameters=[
            OpenApiParameter(
                name="post_id",
                description="Lọc theo bài viết",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="user_id",
                description="Lọc theo người dùng",
                required=False,
                type=int,
            ),
        ],
        tags=["posts"],
    ),
    create=extend_schema(
        summary="Tạo bình luận",
        description="Tạo bình luận mới cho bài viết.",
        examples=[
            OpenApiExample(
                "Mẫu tạo bình luận",
                value={"post": 1, "content": "Bài viết hay quá!"},
                request_only=True,
            )
        ],
        tags=["posts"],
    ),
    retrieve=extend_schema(
        summary="Chi tiết bình luận",
        description="Lấy thông tin chi tiết một bình luận.",
        tags=["posts"],
    ),
    update=extend_schema(
        summary="Cập nhật toàn bộ bình luận",
        description="Chỉ chủ bình luận mới có quyền cập nhật.",
        tags=["posts"],
    ),
    partial_update=extend_schema(
        summary="Cập nhật một phần bình luận",
        description="Chỉ chủ bình luận mới có quyền cập nhật.",
        examples=[
            OpenApiExample(
                "Mẫu sửa bình luận",
                value={"content": "Nội dung bình luận đã sửa"},
                request_only=True,
            )
        ],
        tags=["posts"],
    ),
    destroy=extend_schema(
        summary="Xóa bình luận",
        description="Chỉ chủ bình luận mới có quyền xóa.",
        tags=["posts"],
    ),
)
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
