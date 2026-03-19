from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiExample,
)

from .models import Conversation, ConversationMember, Message
from .serializers import (
    AddMemberSerializer,
    ConversationCreateSerializer,
    ConversationDetailSerializer,
    ConversationMemberDetailSerializer,
    ConversationSerializer,
    ConversationUpdateSerializer,
    ConversationWithJoinedAtSerializer,
    MessageCreateSerializer,
    MessageSerializer,
    MessageUpdateSerializer,
)

def _check_membership(user, conversation):
    if not ConversationMember.objects.filter(
        conversation=conversation, user=user
    ).exists():
        raise permissions.PermissionDenied(
            "You are not a member of this conversation."
        )


def _broadcast_ws(conversation_id, event):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"conversation_{conversation_id}",
        event,
    )


class ConversationMessagesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Danh sách tin nhắn của cuộc hội thoại",
        description="Lấy danh sách tin nhắn trong cuộc hội thoại theo thứ tự thời gian tạo.",
        responses={200: MessageSerializer(many=True)},
    )
    def get(self, request, pk):
        conversation = get_object_or_404(Conversation, pk=pk)
        _check_membership(request.user, conversation)
        messages = Message.objects.filter(conversation=conversation).order_by("created_at")
        return Response(MessageSerializer(messages, many=True).data)

    @extend_schema(
        summary="Gửi tin nhắn trong cuộc hội thoại",
        description="Tạo tin nhắn mới trong cuộc hội thoại. Tin nhắn sẽ được broadcast tới tất cả thành viên đang kết nối WebSocket.",
        request=MessageCreateSerializer,
        responses={201: MessageSerializer},
        examples=[
            OpenApiExample(
                "Mẫu gửi tin nhắn text",
                value={"content": "Xin chào mọi người!"},
                request_only=True,
            ),
            OpenApiExample(
                "Mẫu gửi tin nhắn hình ảnh",
                value={
                    "content": "",
                    "media_url": "https://example.com/photo.jpg",
                    "media_type": "image",
                },
                request_only=True,
            ),
        ],
    )
    def post(self, request, pk):
        conversation = get_object_or_404(Conversation, pk=pk)
        _check_membership(request.user, conversation)

        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=serializer.validated_data["content"],
            media_url=serializer.validated_data.get("media_url"),
            media_type=serializer.validated_data["media_type"],
        )

        _broadcast_ws(pk, {
            "type": "chat.message",
            "id": message.id,
            "conversation_id": pk,
            "sender_id": request.user.id,
            "content": message.content,
            "media_url": message.media_url,
            "media_type": message.media_type,
            "created_at": message.created_at.isoformat(),
        })

        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)

@extend_schema_view(
    get=extend_schema(
        summary="Danh sách cuộc hội thoại",
        description="Lấy danh sách các cuộc hội thoại mà người dùng hiện tại đang tham gia, sắp xếp theo thời gian tham gia mới nhất.",
        responses={200: ConversationWithJoinedAtSerializer(many=True)},
    ),
    post=extend_schema(
        summary="Tạo cuộc hội thoại",
        description="Tạo một cuộc hội thoại mới. Người tạo sẽ được thêm làm thành viên. Có thể truyền `member_ids` để thêm thành viên ngay khi tạo.",
        request=ConversationCreateSerializer,
        responses={201: ConversationWithJoinedAtSerializer},
        examples=[
            OpenApiExample(
                "Mẫu tạo cuộc hội thoại nhóm",
                value={
                    "name": "Nhóm dự án",
                    "is_group": True,
                    "member_ids": [2, 3, 6],
                },
                request_only=True,
            ),
            OpenApiExample(
                "Mẫu tạo cuộc hội thoại riêng",
                value={
                    "name": "",
                    "is_group": False,
                    "member_ids": [2, 3],
                },
                request_only=True,
            ),
        ],
    ),
)
class ConversationView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ConversationWithJoinedAtSerializer
        return ConversationSerializer

    def get_queryset(self):
        return (
            ConversationMember.objects.select_related("conversation")
            .filter(user=self.request.user)
            .order_by("-joined_at")
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

    def create(self, request, *args, **kwargs):
        serializer = ConversationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        conversation = serializer.instance
        membership = ConversationMember.objects.select_related("conversation").get(
            conversation=conversation, user=request.user
        )
        output = ConversationWithJoinedAtSerializer(membership)
        return Response(output.data, status=status.HTTP_201_CREATED)

class ConversationDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _get_conversation(self, pk, user):
        conversation = get_object_or_404(Conversation, pk=pk)
        _check_membership(user, conversation)
        return conversation

    @extend_schema(
        summary="Chi tiết cuộc hội thoại",
        description="Lấy thông tin chi tiết của một cuộc hội thoại. Chỉ thành viên của cuộc hội thoại mới có quyền xem.",
        responses={200: ConversationDetailSerializer},
    )
    def get(self, request, pk):
        conversation = self._get_conversation(pk, request.user)
        return Response(ConversationDetailSerializer(conversation).data)

    @extend_schema(
        summary="Chỉnh sửa thông tin cuộc hội thoại",
        description="Cập nhật tên hoặc loại cuộc hội thoại. Bất kỳ thành viên nào đều có quyền chỉnh sửa.",
        request=ConversationUpdateSerializer,
        responses={200: ConversationDetailSerializer},
        examples=[
            OpenApiExample(
                "Mẫu đổi tên cuộc hội thoại",
                value={"name": "Tên mới"},
                request_only=True,
            ),
        ],
    )
    def patch(self, request, pk):
        conversation = self._get_conversation(pk, request.user)
        serializer = ConversationUpdateSerializer(conversation, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ConversationDetailSerializer(conversation).data)

    @extend_schema(
        summary="Xoá cuộc hội thoại",
        description="Xoá một cuộc hội thoại. Chỉ thành viên của cuộc hội thoại mới có quyền xoá.",
        responses={204: None},
    )
    def delete(self, request, pk):
        conversation = self._get_conversation(pk, request.user)
        conversation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ConversationMembersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _get_conversation(self, pk, user):
        conversation = get_object_or_404(Conversation, pk=pk)
        if not ConversationMember.objects.filter(
            conversation=conversation, user=user
        ).exists():
            raise permissions.PermissionDenied(
                "You are not a member of this conversation."
            )
        return conversation

    @extend_schema(
        summary="Danh sách thành viên cuộc hội thoại",
        description="Lấy danh sách tất cả thành viên trong một cuộc hội thoại.",
        responses={200: ConversationMemberDetailSerializer(many=True)},
    )
    def get(self, request, pk):
        conversation = self._get_conversation(pk, request.user)
        members = ConversationMember.objects.select_related("user").filter(
            conversation=conversation
        )
        serializer = ConversationMemberDetailSerializer(members, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Thêm thành viên vào cuộc hội thoại",
        description="Thêm một người dùng vào cuộc hội thoại bằng `user_id` trong body.",
        request=AddMemberSerializer,
        responses={201: ConversationMemberDetailSerializer},
        examples=[
            OpenApiExample(
                "Mẫu thêm thành viên",
                value={"user_id": 2},
                request_only=True,
            ),
        ],
    )
    def post(self, request, pk):
        conversation = self._get_conversation(pk, request.user)
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

    @extend_schema(
        summary="Xoá thành viên khỏi cuộc hội thoại",
        description="Xoá một thành viên khỏi cuộc hội thoại theo `user_id` trên URL path.",
        responses={204: None},
    )
    def delete(self, request, pk, user_id):
        conversation = get_object_or_404(Conversation, pk=pk)
        _check_membership(request.user, conversation)

        member = get_object_or_404(
            ConversationMember,
            conversation=conversation,
            user_id=user_id,
        )
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MessageDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Chỉnh sửa tin nhắn",
        description="Cập nhật nội dung tin nhắn. Chỉ người gửi mới có quyền chỉnh sửa tin nhắn của mình.",
        request=MessageUpdateSerializer,
        responses={200: MessageSerializer},
        examples=[
            OpenApiExample(
                "Mẫu sửa nội dung tin nhắn",
                value={"content": "Nội dung đã chỉnh sửa"},
                request_only=True,
            ),
        ],
    )
    def patch(self, request, pk, message_id):
        conversation = get_object_or_404(Conversation, pk=pk)
        _check_membership(request.user, conversation)

        message = get_object_or_404(Message, pk=message_id, conversation=conversation)
        if message.sender != request.user:
            raise permissions.PermissionDenied(
                "Chỉ người gửi mới có quyền chỉnh sửa tin nhắn."
            )

        serializer = MessageUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        for field, value in serializer.validated_data.items():
            setattr(message, field, value)
        message.save(update_fields=list(serializer.validated_data.keys()))

        _broadcast_ws(pk, {
            "type": "chat.message_edited",
            "id": message.id,
            "conversation_id": pk,
            "sender_id": message.sender_id,
            "content": message.content,
            "media_url": message.media_url,
            "media_type": message.media_type,
            "created_at": message.created_at.isoformat(),
        })

        return Response(MessageSerializer(message).data)
