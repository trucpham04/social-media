from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import serializers

from .models import Follow, Friend

User = get_user_model()


class FriendRequestCreateSerializer(serializers.Serializer):
    friend_id = serializers.IntegerField()

    def validate_friend_id(self, value):
        user = self.context["request"].user

        if value == user.id:
            raise serializers.ValidationError("You cannot send a friend request to yourself.")

        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("User does not exist.")

        exists_relation = Friend.objects.filter(
            Q(user_id=user.id, friend_id=value) | Q(user_id=value, friend_id=user.id)
        ).exists()

        if exists_relation:
            raise serializers.ValidationError("Friend relationship/request already exists.")

        return value


class FriendRequestSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    user_username = serializers.CharField(source="user.username", read_only=True)
    friend_id = serializers.IntegerField(source="friend.id", read_only=True)
    friend_username = serializers.CharField(source="friend.username", read_only=True)

    class Meta:
        model = Friend
        fields = [
            "id",
            "user_id",
            "user_username",
            "friend_id",
            "friend_username",
            "status",
            "created_at",
        ]


class FollowCreateSerializer(serializers.Serializer):
    followed_id = serializers.IntegerField()

    def validate_followed_id(self, value):
        user = self.context["request"].user

        if value == user.id:
            raise serializers.ValidationError("You cannot follow yourself.")

        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("User does not exist.")

        if Follow.objects.filter(follower=user, followed_id=value).exists():
            raise serializers.ValidationError("You are already following this user.")

        return value


class FollowSerializer(serializers.ModelSerializer):
    follower_id = serializers.IntegerField(source="follower.id", read_only=True)
    follower_username = serializers.CharField(source="follower.username", read_only=True)
    followed_id = serializers.IntegerField(source="followed.id", read_only=True)
    followed_username = serializers.CharField(source="followed.username", read_only=True)

    class Meta:
        model = Follow
        fields = [
            "id",
            "follower_id",
            "follower_username",
            "followed_id",
            "followed_username",
            "created_at",
        ]
