from django.urls import path
from users.views import SignUpView, CustomTokenObtainPairView, GoogleLogin, AuthCheck

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup_view"),
    path(
        "login/",
        CustomTokenObtainPairView.as_view(),
        name="custom_token_obtain_pair",
    ),
    path("auth/", AuthCheck.as_view(), name="auth_check"),
    path("google/", GoogleLogin.as_view(), name="google_login"),
    
]