from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Follow, Friend
from .serializers import (
    FollowCreateSerializer,
    FollowSerializer,
    FriendRequestCreateSerializer,
    FriendRequestSerializer,
)


class FriendRequestCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FriendRequestCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        friend_request = Friend.objects.create(
            user=request.user,
            friend_id=serializer.validated_data["friend_id"],
            status=Friend.STATUS_PENDING,
        )

        Follow.objects.get_or_create(
            follower=request.user,
            followed_id=serializer.validated_data["friend_id"],
        )

        return Response(FriendRequestSerializer(friend_request).data, status=status.HTTP_201_CREATED)


class ReceivedFriendRequestListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        requests = Friend.objects.filter(friend=request.user, status=Friend.STATUS_PENDING)
        return Response(FriendRequestSerializer(requests, many=True).data)


class SentFriendRequestListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        requests = Friend.objects.filter(user=request.user, status=Friend.STATUS_PENDING)
        return Response(FriendRequestSerializer(requests, many=True).data)


class AcceptFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id: int):
        friend_request = Friend.objects.filter(
            id=request_id,
            friend=request.user,
            status=Friend.STATUS_PENDING,
        ).first()

        if not friend_request:
            return Response({"detail": "Friend request not found."}, status=status.HTTP_404_NOT_FOUND)

        friend_request.status = Friend.STATUS_ACCEPTED
        friend_request.save(update_fields=["status"])

        Follow.objects.get_or_create(
            follower=friend_request.user,
            followed=friend_request.friend,
        )
        Follow.objects.get_or_create(
            follower=friend_request.friend,
            followed=friend_request.user,
        )

        return Response(FriendRequestSerializer(friend_request).data)


class RejectFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id: int):
        friend_request = Friend.objects.filter(
            id=request_id,
            friend=request.user,
            status=Friend.STATUS_PENDING,
        ).first()

        if not friend_request:
            return Response({"detail": "Friend request not found."}, status=status.HTTP_404_NOT_FOUND)

        friend_request.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CancelFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, request_id: int):
        friend_request = Friend.objects.filter(
            id=request_id,
            user=request.user,
            status=Friend.STATUS_PENDING,
        ).first()

        if not friend_request:
            return Response({"detail": "Friend request not found."}, status=status.HTTP_404_NOT_FOUND)

        friend_request.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FriendListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        friendships = Friend.objects.filter(
            Q(user=request.user) | Q(friend=request.user),
            status=Friend.STATUS_ACCEPTED,
        ).select_related("user", "friend")

        normalized = []
        for relation in friendships:
            if relation.user_id == request.user.id:
                friend_user = relation.friend
            else:
                friend_user = relation.user

            normalized.append(
                {
                    "id": relation.id,
                    "user_id": request.user.id,
                    "user_username": request.user.username,
                    "friend_id": friend_user.id,
                    "friend_username": friend_user.username,
                    "status": relation.status,
                    "created_at": relation.created_at,
                }
            )

        return Response(normalized)


class UnfriendView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, user_id: int):
        friendship = Friend.objects.filter(
            Q(user=request.user, friend_id=user_id) | Q(user_id=user_id, friend=request.user),
            status=Friend.STATUS_ACCEPTED,
        ).first()

        if not friendship:
            return Response({"detail": "Friend relationship not found."}, status=status.HTTP_404_NOT_FOUND)

        friendship.delete()

        Follow.objects.filter(
            follower=request.user,
            followed_id=user_id,
        ).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FollowCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        follow = Follow.objects.create(
            follower=request.user,
            followed_id=serializer.validated_data["followed_id"],
        )
        return Response(FollowSerializer(follow).data, status=status.HTTP_201_CREATED)


class FollowingListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        follows = Follow.objects.filter(follower=request.user)
        return Response(FollowSerializer(follows, many=True).data)


class FollowerListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        follows = Follow.objects.filter(followed=request.user)
        return Response(FollowSerializer(follows, many=True).data)


class UnfollowView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, user_id: int):
        follow = Follow.objects.filter(follower=request.user, followed_id=user_id).first()

        if not follow:
            return Response({"detail": "Follow relationship not found."}, status=status.HTTP_404_NOT_FOUND)

        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
