from rest_framework import serializers
from .models import Post
from .utils import upload_file_to_s3, delete_file_from_s3


class PostSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    media_file = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = Post
        fields = [
            "id",
            "user_id",
            "username",
            "content",
            "media_url",
            "media_type",
            "visibility",
            "created_at",
            "media_file",
        ]
        read_only_fields = ["id", "created_at", "media_url"]

    def validate_media_type(self, value):
        """Validate media_type matches the file if provided"""
        media_file = self.initial_data.get("media_file")
        if media_file:
            content_type = media_file.content_type
            if content_type.startswith("image/"):
                if value != Post.MEDIA_TYPE_IMAGE:
                    raise serializers.ValidationError(
                        "media_type must be 'image' when uploading an image file"
                    )
            elif content_type.startswith("video/"):
                if value != Post.MEDIA_TYPE_VIDEO:
                    raise serializers.ValidationError(
                        "media_type must be 'video' when uploading a video file"
                    )
        return value

    def create(self, validated_data):
        """Create a new post and upload media to S3 if provided"""
        media_file = validated_data.pop("media_file", None)
        user = self.context["request"].user

        # Upload media to S3 if provided
        if media_file:
            try:
                media_url = upload_file_to_s3(media_file)
                validated_data["media_url"] = media_url
            except Exception as e:
                raise serializers.ValidationError(f"Failed to upload media: {str(e)}")

        post = Post.objects.create(user=user, **validated_data)
        return post

    def update(self, instance, validated_data):
        """Update a post and handle media replacement"""
        media_file = validated_data.pop("media_file", None)

        # If new media is provided, delete old media and upload new one
        if media_file:
            # Delete old media from S3 if it exists
            if instance.media_url:
                delete_file_from_s3(instance.media_url)

            # Upload new media
            try:
                media_url = upload_file_to_s3(media_file)
                validated_data["media_url"] = media_url
            except Exception as e:
                raise serializers.ValidationError(f"Failed to upload media: {str(e)}")

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class PostListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "user_id",
            "username",
            "content",
            "media_url",
            "media_type",
            "visibility",
            "created_at",
        ]
