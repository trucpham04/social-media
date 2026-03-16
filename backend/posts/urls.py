from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PostViewSet
from .interaction_views import PostReportViewSet, LikeViewSet, CommentViewSet

router = DefaultRouter()
router.register(r"", PostViewSet, basename="post")
router.register(r"reports", PostReportViewSet, basename="post-report")
router.register(r"likes", LikeViewSet, basename="like")
router.register(r"comments", CommentViewSet, basename="comment")

urlpatterns = [
    path("", include(router.urls)),
]
