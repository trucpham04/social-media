from django.urls import path

from .views import (
    AcceptFriendRequestView,
    CancelFriendRequestView,
    FollowCreateView,
    FollowerListView,
    FollowingListView,
    FriendListView,
    FriendRequestCreateView,
    ReceivedFriendRequestListView,
    RejectFriendRequestView,
    SentFriendRequestListView,
    UnfollowView,
    UnfriendView,
)

urlpatterns = [
    path("requests/", FriendRequestCreateView.as_view(), name="friend-request-create"),
    path("requests/received/", ReceivedFriendRequestListView.as_view(), name="friend-request-received"),
    path("requests/sent/", SentFriendRequestListView.as_view(), name="friend-request-sent"),
    path("requests/<int:request_id>/accept/", AcceptFriendRequestView.as_view(), name="friend-request-accept"),
    path("requests/<int:request_id>/reject/", RejectFriendRequestView.as_view(), name="friend-request-reject"),
    path("requests/<int:request_id>/cancel/", CancelFriendRequestView.as_view(), name="friend-request-cancel"),
    path("list/", FriendListView.as_view(), name="friend-list"),
    path("<int:user_id>/", UnfriendView.as_view(), name="unfriend"),
    path("follows/", FollowCreateView.as_view(), name="follow-create"),
    path("follows/following/", FollowingListView.as_view(), name="following-list"),
    path("follows/followers/", FollowerListView.as_view(), name="follower-list"),
    path("follows/<int:user_id>/", UnfollowView.as_view(), name="unfollow"),
]
