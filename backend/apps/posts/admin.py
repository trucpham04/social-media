from django.contrib import admin
from django import forms
from django.utils import timezone
from .models import Post, PostReport, Like, Comment
from .utils import upload_file_to_s3, delete_file_from_s3


class PostAdminForm(forms.ModelForm):
    """Custom form for Post admin with file upload support"""
    media_file = forms.FileField(
        required=False,
        help_text="Upload image or video file. This will automatically set the media_url field."
    )

    class Meta:
        model = Post
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make media_url read-only since it's set automatically from media_file
        self.fields["media_url"].widget.attrs["readonly"] = True
        self.fields["media_url"].help_text = "This field is set automatically when you upload a file. To change it, upload a new file."
        
        # Show current media URL if editing
        if self.instance and self.instance.pk and self.instance.media_url:
            self.fields["media_url"].help_text += f"<br>Current: <a href='{self.instance.media_url}' target='_blank'>{self.instance.media_url}</a>"


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    form = PostAdminForm
    list_display = ["id", "user", "media_type", "visibility", "created_at", "has_media"]
    list_display_links = ["id", "user"]  # Make these fields clickable for editing
    list_filter = ["media_type", "visibility", "created_at"]
    search_fields = ["content", "user__username", "user__email"]
    readonly_fields = ["created_at"]
    list_per_page = 25  # Show 25 items per page
    fieldsets = (
        ("Basic Information", {
            "fields": ("user", "content", "visibility")
        }),
        ("Media", {
            "fields": ("media_file", "media_type", "media_url"),
            "description": "Upload a file to automatically set media_url. Leave media_file empty to keep existing media_url."
        }),
        ("Metadata", {
            "fields": ("created_at",)
        }),
    )

    def has_media(self, obj):
        """Display whether post has media"""
        return bool(obj.media_url)
    has_media.boolean = True
    has_media.short_description = "Has Media"

    def save_model(self, request, obj, form, change):
        """Override save to handle file upload to S3"""
        media_file = form.cleaned_data.get("media_file")

        # If a new file is uploaded
        if media_file:
            # Delete old media from S3 if updating and old media exists
            if change and obj.pk and obj.media_url:
                try:
                    delete_file_from_s3(obj.media_url)
                except Exception:
                    pass  # Continue even if deletion fails

            # Upload new file to S3
            try:
                media_url = upload_file_to_s3(media_file)
                obj.media_url = media_url

                # Auto-detect media type based on file content type
                content_type = getattr(media_file, "content_type", "")
                if content_type.startswith("image/"):
                    obj.media_type = Post.MEDIA_TYPE_IMAGE
                elif content_type.startswith("video/"):
                    obj.media_type = Post.MEDIA_TYPE_VIDEO
                # If media_type is still text and we have a file, default to image
                elif obj.media_type == Post.MEDIA_TYPE_TEXT:
                    # Try to detect from filename
                    filename = getattr(media_file, "name", "").lower()
                    if any(ext in filename for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]):
                        obj.media_type = Post.MEDIA_TYPE_IMAGE
                    elif any(ext in filename for ext in [".mp4", ".avi", ".mov", ".webm"]):
                        obj.media_type = Post.MEDIA_TYPE_VIDEO
            except Exception as e:
                from django.contrib import messages
                messages.error(request, f"Failed to upload media to S3: {str(e)}")
                # Don't save if upload fails
                return

        # If no file is uploaded and we're creating a new post, ensure media_type is set
        elif not change and not media_file:
            if not obj.media_type:
                obj.media_type = Post.MEDIA_TYPE_TEXT

        super().save_model(request, obj, form, change)


@admin.register(PostReport)
class PostReportAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "post",
        "reporter",
        "review_status",
        "reviewed_by",
        "reviewed_at",
        "created_at",
    ]
    list_display_links = ["id", "post"]  # Make these fields clickable for editing
    list_filter = ["review_status", "created_at", "reviewed_at"]
    search_fields = ["reason", "reporter__username", "post__id"]
    readonly_fields = ["created_at"]
    list_per_page = 25
    fieldsets = (
        ("Report Information", {"fields": ("post", "reporter", "reason", "created_at")}),
        (
            "Review",
            {
                "fields": (
                    "review_status",
                    "reviewed_by",
                    "reviewed_at",
                )
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        """Set reviewed_by and reviewed_at when status changes"""
        if change and "review_status" in form.changed_data:
            if obj.review_status != PostReport.REVIEW_STATUS_PENDING:
                if not obj.reviewed_by:
                    obj.reviewed_by = request.user
                if not obj.reviewed_at:
                    obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "post", "reaction", "created_at"]
    list_display_links = ["id", "user", "post"]  # Make these fields clickable for editing
    list_filter = ["reaction", "created_at"]
    search_fields = ["user__username", "post__id"]
    readonly_fields = ["created_at"]
    list_per_page = 25


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["id", "post", "user", "content_preview", "created_at"]
    list_display_links = ["id", "post", "user"]  # Make these fields clickable for editing
    list_filter = ["created_at"]
    search_fields = ["content", "user__username", "post__id"]
    readonly_fields = ["created_at"]
    list_per_page = 25

    def content_preview(self, obj):
        """Show first 50 characters of content"""
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

    content_preview.short_description = "Content"
