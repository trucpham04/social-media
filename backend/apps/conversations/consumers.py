from __future__ import annotations

import json
from collections import defaultdict
from typing import Dict, Set

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

from .auth import authenticate_scope
from .models import Conversation, ConversationMember, Message

active_connections_by_conversation: Dict[int, Set[str]] = defaultdict(set)
active_connections_by_user: Dict[int, Set[str]] = defaultdict(set)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self) -> None:
        self.conversation_id = int(self.scope["url_route"]["kwargs"]["conversation_id"])
        user, _ = await sync_to_async(authenticate_scope)(self.scope)

        if user is None or isinstance(user, AnonymousUser):
            await self.close(code=4401)
            return

        self.user = user

        is_member = await sync_to_async(
            ConversationMember.objects.filter(
                conversation_id=self.conversation_id, user=self.user
            ).exists
        )()
        if not is_member:
            await self.close(code=4403)
            return

        self.group_name = f"conversation_{self.conversation_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)

        active_connections_by_conversation[self.conversation_id].add(self.channel_name)
        active_connections_by_user[self.user.id].add(self.channel_name)

        await self.accept()

    async def disconnect(self, close_code: int) -> None:
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

        conv_set = active_connections_by_conversation.get(
            getattr(self, "conversation_id", None)
        )
        if conv_set and self.channel_name in conv_set:
            conv_set.discard(self.channel_name)
            if not conv_set:
                active_connections_by_conversation.pop(self.conversation_id, None)

        user = getattr(self, "user", None)
        if user is not None:
            user_set = active_connections_by_user.get(user.id)
            if user_set and self.channel_name in user_set:
                user_set.discard(self.channel_name)
                if not user_set:
                    active_connections_by_user.pop(user.id, None)

    async def receive(self, text_data: str | bytes | None = None, bytes_data=None):
        if text_data is None:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send_json({"type": "error", "message": "Invalid JSON"})
            return

        content = data.get("content", "") or ""
        media_url = data.get("media_url")
        media_type = data.get("media_type") or Message.MEDIA_TYPE_TEXT

        if media_type == Message.MEDIA_TYPE_TEXT and not content.strip():
            await self.send_json(
                {"type": "error", "message": "content is required for text messages"}
            )
            return

        if media_type in (
            Message.MEDIA_TYPE_IMAGE,
            Message.MEDIA_TYPE_VIDEO,
        ) and not media_url:
            await self.send_json(
                {"type": "error", "message": "media_url is required for media messages"}
            )
            return

        message = await sync_to_async(Message.objects.create)(
            conversation_id=self.conversation_id,
            sender=self.user,
            content=content,
            media_url=media_url,
            media_type=media_type,
        )

        payload = {
            "type": "chat.message",
            "id": message.id,
            "conversation_id": self.conversation_id,
            "sender_id": self.user.id,
            "content": message.content,
            "media_url": message.media_url,
            "media_type": message.media_type,
            "created_at": message.created_at.isoformat(),
        }

        await self.channel_layer.group_send(self.group_name, payload)

    async def chat_message(self, event):
        await self.send_json(
            {
                "type": "message",
                "id": event["id"],
                "conversation_id": event["conversation_id"],
                "sender_id": event["sender_id"],
                "content": event["content"],
                "media_url": event["media_url"],
                "media_type": event["media_type"],
                "created_at": event["created_at"],
            }
        )

    async def chat_message_edited(self, event):
        await self.send_json(
            {
                "type": "message_edited",
                "id": event["id"],
                "conversation_id": event["conversation_id"],
                "sender_id": event["sender_id"],
                "content": event["content"],
                "media_url": event["media_url"],
                "media_type": event["media_type"],
                "created_at": event["created_at"],
            }
        )

    async def send_json(self, content, close=False):
        await self.send(text_data=json.dumps(content, ensure_ascii=False), close=close)

