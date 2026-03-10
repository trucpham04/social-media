from django.conf import settings
from django.db import models


class Conversation(models.Model):
    name = models.CharField(max_length=255, blank=True, default="")
    is_group = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Conversation #{self.pk}"


class ConversationMember(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="members",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversation_memberships",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("conversation", "user")

    def __str__(self) -> str:
        return f"{self.user} in {self.conversation}"


class Message(models.Model):
    MEDIA_TYPE_TEXT = "text"
    MEDIA_TYPE_IMAGE = "image"
    MEDIA_TYPE_VIDEO = "video"

    MEDIA_TYPE_CHOICES = [
        (MEDIA_TYPE_TEXT, "Text"),
        (MEDIA_TYPE_IMAGE, "Image"),
        (MEDIA_TYPE_VIDEO, "Video"),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages_sent",
    )
    content = models.TextField()
    media_url = models.URLField(blank=True, null=True)
    media_type = models.CharField(
        max_length=10,
        choices=MEDIA_TYPE_CHOICES,
        default=MEDIA_TYPE_TEXT,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Message #{self.pk} in {self.conversation}"
