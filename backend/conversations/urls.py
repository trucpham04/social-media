from django.urls import path

from .views import (
    ConversationDeleteView,
    ConversationDetailView,
    ConversationListCreateView,
    ConversationMemberAddView,
    ConversationMemberRemoveView,
    ConversationMembersListView,
    ConversationMessagesListView,
    UserConversationsListView,
)

app_name = "conversations"

urlpatterns = [
    path(
        "",
        UserConversationsListView.as_view(),
        name="user-conversations",
    ),
    path(
        "list-create/",
        ConversationListCreateView.as_view(),
        name="conversation-list-create",
    ),
    path(
        "<int:conversation_id>/messages/",
        ConversationMessagesListView.as_view(),
        name="conversation-messages",
    ),
    path(
        "<int:pk>/",
        ConversationDetailView.as_view(),
        name="conversation-detail",
    ),
    path(
        "<int:pk>/delete/",
        ConversationDeleteView.as_view(),
        name="conversation-delete",
    ),
    path(
        "<int:pk>/members/",
        ConversationMembersListView.as_view(),
        name="conversation-members",
    ),
    path(
        "<int:pk>/members/add/",
        ConversationMemberAddView.as_view(),
        name="conversation-member-add",
    ),
    path(
        "<int:pk>/members/<int:user_id>/remove/",
        ConversationMemberRemoveView.as_view(),
        name="conversation-member-remove",
    ),
]

