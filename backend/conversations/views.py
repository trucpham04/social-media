from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Conversation, ConversationMember, Message
from .serializers import (
    AddMemberSerializer,
    ConversationDetailSerializer,
    ConversationMemberDetailSerializer,
    ConversationMemberSerializer,
    ConversationSerializer,
    MessageSerializer,
)


class UserConversationsListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ConversationMemberSerializer

    def get_queryset(self):
        return (
            ConversationMember.objects.select_related("conversation")
            .filter(user=self.request.user)
            .order_by("-joined_at")
        )


class ConversationMessagesListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MessageSerializer

    def get_queryset(self):
        conversation_id = self.kwargs["conversation_id"]
        return Message.objects.filter(conversation_id=conversation_id).order_by(
            "created_at"
        )


class ConversationListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ConversationSerializer

    def get_queryset(self):
        return (
            Conversation.objects.filter(members__user=self.request.user)
            .distinct()
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        member_ids = self.request.data.get("member_ids", [])
        conversation = serializer.save()
        ConversationMember.objects.get_or_create(
            conversation=conversation, user=self.request.user
        )
        for user_id in member_ids:
            ConversationMember.objects.get_or_create(
                conversation=conversation, user_id=user_id
            )


class ConversationDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ConversationDetailSerializer
    queryset = Conversation.objects.all()

    def get_object(self):
        conversation = super().get_object()
        if not ConversationMember.objects.filter(
            conversation=conversation, user=self.request.user
        ).exists():
            raise permissions.PermissionDenied(
                "You are not a member of this conversation."
            )
        return conversation


class ConversationDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Conversation.objects.all()

    def get_object(self):
        conversation = super().get_object()
        if not ConversationMember.objects.filter(
            conversation=conversation, user=self.request.user
        ).exists():
            raise permissions.PermissionDenied(
                "You are not a member of this conversation."
            )
        return conversation


class ConversationMembersListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ConversationMemberDetailSerializer

    def get_queryset(self):
        conversation = get_object_or_404(
            Conversation, pk=self.kwargs["pk"]
        )
        if not ConversationMember.objects.filter(
            conversation=conversation, user=self.request.user
        ).exists():
            raise permissions.PermissionDenied(
                "You are not a member of this conversation."
            )
        return ConversationMember.objects.select_related("user").filter(
            conversation=conversation
        )


class ConversationMemberAddView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        conversation = get_object_or_404(Conversation, pk=pk)
        if not ConversationMember.objects.filter(
            conversation=conversation, user=request.user
        ).exists():
            raise permissions.PermissionDenied(
                "You are not a member of this conversation."
            )

        serializer = AddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = serializer.validated_data["user_id"]

        member, created = ConversationMember.objects.get_or_create(
            conversation=conversation, user_id=user_id
        )
        if not created:
            return Response(
                {"detail": "User is already a member of this conversation."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            ConversationMemberDetailSerializer(member).data,
            status=status.HTTP_201_CREATED,
        )


class ConversationMemberRemoveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk, user_id):
        conversation = get_object_or_404(Conversation, pk=pk)
        if not ConversationMember.objects.filter(
            conversation=conversation, user=request.user
        ).exists():
            raise permissions.PermissionDenied(
                "You are not a member of this conversation."
            )

        member = get_object_or_404(
            ConversationMember,
            conversation=conversation,
            user_id=user_id,
        )
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
