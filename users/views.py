from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from users.serializers import RegisterSerializer, UserProfileSerializer, ChangePasswordSerializer

# Rate limiters
class RegisterThrottle(AnonRateThrottle):
    scope = "register"

class LoginThrottle(AnonRateThrottle):
    scope = "login"

class LogoutThrottle(UserRateThrottle):
    scope = "logout"

class PasswordChangeThrottle(UserRateThrottle):
    scope = "password_change"

class ProfileViewThrottle(UserRateThrottle):
    scope = "profile_view"

class ProfileUpdateThrottle(UserRateThrottle):
    scope = "profile_update"


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [RegisterThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "User registered successfully",
                "email": user.email
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """View and update user profile"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        throttle = ProfileViewThrottle()
        if not throttle.allow_request(request, self):
            return Response(
                {"detail": "Rate limit exceeded. Try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        throttle = ProfileUpdateThrottle()
        if not throttle.allow_request(request, self):
            return Response(
                {"detail": "Rate limit exceeded. Try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated successfully", "data": serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """Change user password and invalidate tokens"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [PasswordChangeThrottle]

    def post(self, request):
        serializer = ChangePasswordSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Password changed successfully. Please login again with your new password."
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """Logout and blacklist refresh token"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [LogoutThrottle]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {"detail": "Refresh token is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"message": "Successfully logged out."},
                status=status.HTTP_205_RESET_CONTENT
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )