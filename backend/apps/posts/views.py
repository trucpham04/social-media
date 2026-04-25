from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from rest_framework.views import APIView

from apps.friends.models import Friend

from .models import Post
from .serializers import PostSerializer, PostListSerializer
from .utils import delete_file_from_s3


@extend_schema_view(
    list=extend_schema(
        summary="Danh sách bài viết",
        description="Lấy danh sách bài viết theo quyền xem và bộ lọc.",
        parameters=[
            OpenApiParameter(
                name="visibility",
                description="Lọc theo quyền riêng tư: public | friends | private",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="user_id",
                description="Lọc theo tác giả bài viết",
                required=False,
                type=int,
            ),
        ],
        tags=["posts"],
    ),
    retrieve=extend_schema(
        summary="Chi tiết bài viết",
        description="Lấy thông tin chi tiết một bài viết.",
        tags=["posts"],
    ),
    create=extend_schema(
        summary="Tạo bài viết",
        description="Tạo bài viết mới, có thể kèm media_file để upload lên S3.",
        request=PostSerializer,
        examples=[
            OpenApiExample(
                "Mẫu tạo bài viết text",
                value={
                    "content": "Hello world",
                    "media_type": "text",
                    "visibility": "public",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Mẫu tạo bài viết ảnh",
                value={
                    "content": "Ảnh mới",
                    "media_type": "image",
                    "visibility": "friends",
                },
                request_only=True,
            ),
        ],
        tags=["posts"],
    ),
    update=extend_schema(
        summary="Cập nhật toàn bộ bài viết",
        description="Chỉ chủ bài viết mới có quyền cập nhật.",
        request=PostSerializer,
        tags=["posts"],
    ),
    partial_update=extend_schema(
        summary="Cập nhật một phần bài viết",
        description="Chỉ chủ bài viết mới có quyền cập nhật.",
        request=PostSerializer,
        examples=[
            OpenApiExample(
                "Mẫu cập nhật content",
                value={"content": "Nội dung đã chỉnh sửa"},
                request_only=True,
            ),
        ],
        tags=["posts"],
    ),
    destroy=extend_schema(
        summary="Xóa bài viết",
        description="Xóa bài viết và media trên S3 (nếu có). Chỉ chủ bài viết được phép.",
        tags=["posts"],
    ),
)
class PostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Post CRUD operations.
    Requires authentication for all operations.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
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
    @extend_schema(
        summary="Danh sách bài viết của tôi",
        description="Lấy tất cả bài viết của người dùng đang đăng nhập.",
        tags=["posts"],
    )
    def my_posts(self, request):
        """Get all posts by the authenticated user"""
        posts = self.get_queryset().filter(user=request.user)
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"])
    def new_feed(self, request):
        user = request.user

        # Lấy danh sách ID bạn bè đã accepted
        friend_pairs = Friend.objects.filter(
            Q(user=user, status=Friend.STATUS_ACCEPTED)
            | Q(friend=user, status=Friend.STATUS_ACCEPTED)
        ).values_list("user_id", "friend_id")

        friend_ids = {uid for pair in friend_pairs for uid in pair if uid != user.id}

        # Lấy bài viết của chính user + bạn bè, sắp xếp mới nhất trước
        posts = (
            Post.objects.filter(Q(user=user) | Q(user_id__in=friend_ids))
            .select_related("user")
            .order_by("-created_at")
        )

        serializer = PostListSerializer(posts, many=True)
        return Response(serializer.data)

class PostAdvanceSearchView(APIView):

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        queryset = Post.objects.select_related("user").all()

        keyword = request.query_params.get("keyword", "")

        if keyword:
            queryset = queryset.filter(
                Q(content__icontains=keyword) | Q(user__username__icontains=keyword)
            )
        author_id = request.query_params.get("author_id", None)
        if author_id:
            queryset = queryset.filter(user_id=author_id)
        min_likes = request.query_params.get("min_likes", None)
        if min_likes is not None:
            queryset = queryset.annotate(like_count=Count("likes")).filter(like_count__gte=min_likes)
        

        serializer = PostSerializer(queryset, many=True)

        return Response(serializer.data)
