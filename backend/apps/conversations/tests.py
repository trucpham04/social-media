from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase

from config.asgi import application
from conversations.models import Conversation, ConversationMember, Message


class ChatConsumerTests(TransactionTestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="alice", email="alice@example.com", password="password123"
        )
        self.conversation = Conversation.objects.create(is_group=False)
        ConversationMember.objects.create(
            conversation=self.conversation, user=self.user
        )

    def _build_ws_url(self, conversation_id, token=None):
        base = f"/ws/conversations/{conversation_id}/"
        if token:
            return f"{base}?token={token}"
        return base

    def test_connect_without_token_fails(self):
        async def inner():
            communicator = WebsocketCommunicator(
                application, self._build_ws_url(self.conversation.id)
            )
            connected, _ = await communicator.connect()
            assert not connected
            await communicator.disconnect()

        async_to_sync(inner)()

