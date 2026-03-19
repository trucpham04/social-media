from django.urls import path

from .views import (
    ConversationDetailView,
    ConversationView,
    ConversationMembersView,
    ConversationMemberRemoveView,
    ConversationMessagesView,
    MessageDetailView,
)

app_name = "conversations"

urlpatterns = [
    path(
        "",
        ConversationView.as_view(),
        name="conversation",
    ),
    path(
        "<int:pk>/",
        ConversationDetailView.as_view(),
        name="conversation-detail",
    ),
    path(
        "<int:pk>/messages/",
        ConversationMessagesView.as_view(),
        name="conversation-messages",
    ),
    path(
        "<int:pk>/messages/<int:message_id>/",
        MessageDetailView.as_view(),
        name="conversation-message-detail",
    ),
    path(
        "<int:pk>/members/",
        ConversationMembersView.as_view(),
        name="conversation-members",
    ),
    path(
        "<int:pk>/members/<int:user_id>/",
        ConversationMemberRemoveView.as_view(),
        name="conversation-member",
    ),
]

