from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PostReport, Like, Comment, Post

User = get_user_model()


class PostReportSerializer(serializers.ModelSerializer):
    reporter_id = serializers.IntegerField(source="reporter.id", read_only=True)
    reporter_username = serializers.CharField(source="reporter.username", read_only=True)
    post_id = serializers.PrimaryKeyRelatedField(
        queryset=Post.objects.all(), source="post"
    )
    reviewed_by_id = serializers.IntegerField(
        source="reviewed_by.id", read_only=True, allow_null=True
    )
    reviewed_by_username = serializers.CharField(
        source="reviewed_by.username", read_only=True, allow_null=True
    )

    class Meta:
        model = PostReport
        fields = [
            "id",
            "post_id",
            "reporter_id",
            "reporter_username",
            "reason",
            "review_status",
            "reviewed_by_id",
            "reviewed_by_username",
            "reviewed_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "reporter_id",
            "reporter_username",
            "review_status",
            "reviewed_by_id",
            "reviewed_by_username",
            "reviewed_at",
            "created_at",
        ]

    def create(self, validated_data):
        """Create a report - only authenticated users can report"""
        validated_data["reporter"] = self.context["request"].user
        return super().create(validated_data)


class PostReportUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin to update report status"""
    reviewed_by_id = serializers.IntegerField(
        source="reviewed_by.id", read_only=True, allow_null=True
    )
    reviewed_by_username = serializers.CharField(
        source="reviewed_by.username", read_only=True, allow_null=True
    )

    class Meta:
        model = PostReport
        fields = [
            "id",
            "post_id",
            "reporter_id",
            "reason",
            "review_status",
            "reviewed_by_id",
            "reviewed_by_username",
            "reviewed_at",
            "created_at",
        ]
        read_only_fields = ["id", "post_id", "reporter_id", "reason", "created_at"]


class LikeSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    post_id = serializers.PrimaryKeyRelatedField(
        queryset=Post.objects.all(), source="post"
    )

    class Meta:
        model = Like
        fields = ["user_id", "username", "post_id", "reaction", "created_at"]
        read_only_fields = ["user_id", "username", "created_at"]

    def create(self, validated_data):
        """Create or update like - user is set from request"""
        user = self.context["request"].user
        post = validated_data["post"]

        # Get or create like (update if exists)
        like, created = Like.objects.get_or_create(
            user=user, post=post, defaults={"reaction": validated_data["reaction"]}
        )

        if not created:
            # Update reaction if like already exists
            like.reaction = validated_data["reaction"]
            like.save()

        return like


class CommentSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    post_id = serializers.PrimaryKeyRelatedField(
        queryset=Post.objects.all(), source="post"
    )

    class Meta:
        model = Comment
        fields = ["id", "post_id", "user_id", "username", "content", "created_at"]
        read_only_fields = ["id", "user_id", "username", "created_at"]

    def create(self, validated_data):
        """Create comment - user is set from request"""
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class CommentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "user_id", "username", "content", "created_at"]
