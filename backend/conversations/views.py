from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiExample,
    OpenApiParameter,
)

from .models import Conversation, ConversationMember, Message
from .serializers import (
    AddMemberSerializer,
    ConversationDetailSerializer,
    ConversationMemberDetailSerializer,
    ConversationCreateSerializer,
    ConversationSerializer,
    ConversationWithJoinedAtSerializer,
    MessageSerializer,
)

@extend_schema_view(
    get=extend_schema(
        summary="Danh sách tin nhắn của cuộc hội thoại",
        description="Lấy danh sách tin nhắn trong cuộc hội thoại theo thứ tự thời gian tạo.",
        responses={200: MessageSerializer(many=True)},
    ),
)
class ConversationMessagesView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MessageSerializer

    def get_queryset(self):
        conversation_id = self.kwargs["pk"]
        return Message.objects.filter(conversation_id=conversation_id).order_by(
            "created_at"
        )

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

@extend_schema_view(
    get=extend_schema(
        summary="Chi tiết cuộc hội thoại",
        description="Lấy thông tin chi tiết của một cuộc hội thoại. Chỉ thành viên của cuộc hội thoại mới có quyền xem.",
        responses={200: ConversationDetailSerializer},
    ),
    delete=extend_schema(
        summary="Xoá cuộc hội thoại",
        description="Xoá một cuộc hội thoại. Chỉ thành viên của cuộc hội thoại mới có quyền xoá.",
        responses={204: None},
    ),
)
class ConversationDetailView(generics.RetrieveDestroyAPIView):
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
        parameters=[
            OpenApiParameter(
                name="user_id",
                location=OpenApiParameter.PATH,
                description="ID của người dùng cần xoá",
                type=int,
            ),
        ],
        responses={204: None},
    )
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
