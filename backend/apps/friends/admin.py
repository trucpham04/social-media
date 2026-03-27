from django.contrib import admin

from .models import Friend, Follow


@admin.register(Friend)
class FriendAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "friend", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["user__username", "friend__username", "user__email", "friend__email"]


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ["id", "follower", "followed", "created_at"]
    search_fields = ["follower__username", "followed__username", "follower__email", "followed__email"]
