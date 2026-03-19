from rest_framework import serializers

from .models import Conversation, ConversationMember, Message


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ["id", "name", "is_group", "created_at"]

class ConversationCreateSerializer(serializers.ModelSerializer):
    member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=[],
    )

    class Meta:
        model = Conversation
        fields = ["name", "is_group", "member_ids"]

    def create(self, validated_data):
        validated_data.pop("member_ids", [])
        return super().create(validated_data)

class ConversationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ["id", "name", "is_group", "created_at"]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            "id",
            "conversation_id",
            "sender_id",
            "content",
            "media_url",
            "media_type",
            "created_at",
        ]


class ConversationWithJoinedAtSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="conversation.id", read_only=True)
    name = serializers.CharField(source="conversation.name", read_only=True)
    is_group = serializers.BooleanField(source="conversation.is_group", read_only=True)
    created_at = serializers.DateTimeField(source="conversation.created_at", read_only=True)

    class Meta:
        model = ConversationMember
        fields = ["id", "name", "is_group", "created_at", "joined_at"]


class ConversationMemberDetailSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = ConversationMember
        fields = ["id", "user_id", "username", "email", "joined_at"]


class MessageCreateSerializer(serializers.Serializer):
    content = serializers.CharField(required=False, default="", allow_blank=True)
    media_url = serializers.URLField(required=False, allow_null=True, default=None)
    media_type = serializers.ChoiceField(
        choices=Message.MEDIA_TYPE_CHOICES,
        default=Message.MEDIA_TYPE_TEXT,
    )

    def validate(self, attrs):
        media_type = attrs.get("media_type", Message.MEDIA_TYPE_TEXT)
        content = attrs.get("content", "")
        media_url = attrs.get("media_url")

        if media_type == Message.MEDIA_TYPE_TEXT and not content.strip():
            raise serializers.ValidationError(
                {"content": "Nội dung không được để trống với tin nhắn dạng text."}
            )
        if media_type in (Message.MEDIA_TYPE_IMAGE, Message.MEDIA_TYPE_VIDEO) and not media_url:
            raise serializers.ValidationError(
                {"media_url": "media_url là bắt buộc với tin nhắn dạng media."}
            )
        return attrs


class MessageUpdateSerializer(serializers.Serializer):
    content = serializers.CharField(required=False, allow_blank=True)
    media_url = serializers.URLField(required=False, allow_null=True)
    media_type = serializers.ChoiceField(
        choices=Message.MEDIA_TYPE_CHOICES,
        required=False,
    )

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("Cần ít nhất một trường để cập nhật.")
        return attrs


class ConversationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ["name", "is_group"]
        extra_kwargs = {
            "name": {"required": False},
            "is_group": {"required": False},
        }


class AddMemberSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()

