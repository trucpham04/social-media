from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import RegisterSerializer

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Đăng ký người dùng mới",
        description="Tạo tài khoản mới bằng cách cung cấp username, email và mật khẩu.",
        request=RegisterSerializer,
        responses={
            201: RegisterSerializer,
        },
        examples=[
            OpenApiExample(
                "Mẫu đăng ký",
                value={
                    "username": "testuser",
                    "email": "test@example.com",
                    "password": "StrongPass123!",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Kết quả thành công",
                value={"id": 1, "username": "testuser", "email": "test@example.com"},
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Đăng nhập",
        description="Lấy Access Token và Refresh Token bằng username và password.",
        examples=[
            OpenApiExample(
                "Mẫu đăng nhập",
                value={"username": "testuser", "password": "StrongPass123!"},
                request_only=True,
            ),
        ]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class RefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        summary="Làm mới Access Token",
        description="Sử dụng Refresh Token để lấy một Access Token mới khi token cũ hết hạn.",
        examples=[
            OpenApiExample(
                "Mẫu làm mới",
                value={"refresh": "<refresh_token>"},
                request_only=True,
            ),
        ]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)