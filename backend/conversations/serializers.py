from rest_framework import serializers

from .models import Conversation, ConversationMember, Message


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ["id", "name", "is_group", "created_at"]


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


class ConversationMemberSerializer(serializers.ModelSerializer):
    conversation = ConversationSerializer(read_only=True)

    class Meta:
        model = ConversationMember
        fields = ["id", "conversation", "joined_at"]


class ConversationMemberDetailSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = ConversationMember
        fields = ["id", "user_id", "username", "email", "joined_at"]


class AddMemberSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()

