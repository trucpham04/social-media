from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Post(models.Model):
    MEDIA_TYPE_TEXT = "text"
    MEDIA_TYPE_IMAGE = "image"
    MEDIA_TYPE_VIDEO = "video"

    MEDIA_TYPE_CHOICES = [
        (MEDIA_TYPE_TEXT, "Text"),
        (MEDIA_TYPE_IMAGE, "Image"),
        (MEDIA_TYPE_VIDEO, "Video"),
    ]

    VISIBILITY_PUBLIC = "public"
    VISIBILITY_FRIENDS = "friends"
    VISIBILITY_PRIVATE = "private"

    VISIBILITY_CHOICES = [
        (VISIBILITY_PUBLIC, "Public"),
        (VISIBILITY_FRIENDS, "Friends"),
        (VISIBILITY_PRIVATE, "Private"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="posts", db_column="user_id"
    )
    content = models.TextField(blank=True, null=True)
    media_url = models.URLField(blank=True, null=True)
    media_type = models.CharField(
        max_length=20, choices=MEDIA_TYPE_CHOICES, default=MEDIA_TYPE_TEXT
    )
    visibility = models.CharField(
        max_length=20, choices=VISIBILITY_CHOICES, default=VISIBILITY_PUBLIC
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "posts"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Post {self.id} by {self.user.username}"


class PostReport(models.Model):
    REVIEW_STATUS_PENDING = "pending"
    REVIEW_STATUS_APPROVED = "approved"
    REVIEW_STATUS_REJECTED = "rejected"

    REVIEW_STATUS_CHOICES = [
        (REVIEW_STATUS_PENDING, "Pending"),
        (REVIEW_STATUS_APPROVED, "Approved"),
        (REVIEW_STATUS_REJECTED, "Rejected"),
    ]

    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="reports", db_column="post_id"
    )
    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reports_made",
        db_column="reporter_id",
    )
    reason = models.TextField()
    review_status = models.CharField(
        max_length=20,
        choices=REVIEW_STATUS_CHOICES,
        default=REVIEW_STATUS_PENDING,
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports_reviewed",
        db_column="reviewed_by",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "post_reports"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Report {self.id} on Post {self.post.id} by {self.reporter.username}"


class Like(models.Model):
    REACTION_LIKE = "like"
    REACTION_LOVE = "love"
    REACTION_HAHA = "haha"
    REACTION_ANGRY = "angry"

    REACTION_CHOICES = [
        (REACTION_LIKE, "Like"),
        (REACTION_LOVE, "Love"),
        (REACTION_HAHA, "Haha"),
        (REACTION_ANGRY, "Angry"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="likes", db_column="user_id"
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="likes", db_column="post_id"
    )
    reaction = models.CharField(
        max_length=20, choices=REACTION_CHOICES, default=REACTION_LIKE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "likes"
        unique_together = [["user", "post"]]  # One like per user per post
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} {self.reaction} Post {self.post.id}"


class Comment(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments", db_column="post_id"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        db_column="user_id",
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "comments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Comment {self.id} on Post {self.post.id} by {self.user.username}"
