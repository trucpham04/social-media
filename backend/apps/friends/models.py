from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import F, Q

User = get_user_model()


class Friend(models.Model):
    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_ACCEPTED, "Accepted"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="friend_requests_sent", db_column="user_id"
    )
    friend = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="friend_requests_received", db_column="friend_id"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "friends"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "friend"], name="unique_friend_request"),
            models.CheckConstraint(check=~Q(user=F("friend")), name="friends_not_self"),
        ]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["friend", "status"]),
        ]

    def __str__(self):
        return f"{self.user_id} -> {self.friend_id} ({self.status})"


class Follow(models.Model):
    follower = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="following_relations", db_column="follower_id"
    )
    followed = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="follower_relations", db_column="followed_id"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "follows"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["follower", "followed"], name="unique_follow_relation"),
            models.CheckConstraint(check=~Q(follower=F("followed")), name="follows_not_self"),
        ]
        indexes = [
            models.Index(fields=["follower"]),
            models.Index(fields=["followed"]),
        ]

    def __str__(self):
        return f"{self.follower_id} follows {self.followed_id}"
