from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PostViewSet, PostAdvanceSearchView
from .interaction_views import PostReportViewSet, LikeViewSet, CommentViewSet

router = DefaultRouter()
# Prefix "" must be last: else /comments/ is routed as Post pk="comments".
router.register(r"reports", PostReportViewSet, basename="post-report")
router.register(r"likes", LikeViewSet, basename="like")
router.register(r"comments", CommentViewSet, basename="comment")
router.register(r"", PostViewSet, basename="post")

urlpatterns = [
    path("advance-search/", PostAdvanceSearchView.as_view(), name="post-advance-search"),
    path("", include(router.urls)),
]
