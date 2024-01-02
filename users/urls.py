from django.urls import path
from users.views import SignUpView, CustomTokenObtainPairView, AuthCheck, GenerateVideoView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup_view"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "login/",
        CustomTokenObtainPairView.as_view(),
        name="custom_token_obtain_pair",
    ),
    path("auth/", AuthCheck.as_view(), name="auth_check"),
    path("generate/", GenerateVideoView.as_view(), name="generate_video_view"),
]