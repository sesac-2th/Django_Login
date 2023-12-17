from django.contrib.auth import authenticate
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from users.serializers import UserSerializer, CustomTokenObtainPairSerializer
from users.models import User
from django.contrib.auth.hashers import make_password
import requests


GOOGLE_API_KEY = "1096551886413-j78gem487no6jg5jef4lk4abqdpfa9uq.apps.googleusercontent.com"

class SignUpView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        password2 = request.data.get("password2")  # 2차 비밀번호 입력
        gender = request.data.get("gender")

        if email is None or "@" not in email or password is None or len(password) < 8:
            return Response(
                {"error": "이메일과 비밀번호는 필수이며, 이메일에는 '@'가 포함되어야 하고, 비밀번호는 8자 이상이어야 합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if password != password2:
            return Response(
                {"error": "비밀번호가 일치하지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "이미 존재하는 이메일입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        password = make_password(password)
        user = User.objects.create(email=email, password=password, gender=gender)
        serializer = UserSerializer(user)
        response_data = serializer.data
        response_data['gender'] = gender
        print("res: ", response_data)
        return Response(response_data, status=status.HTTP_201_CREATED)
    
class AuthCheck(APIView):
    # authentication_classes = [JSONWebTokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        # 여기에서는 별다른 로직을 추가하여 인증을 확인하거나 처리합니다.
        # 이 예제에서는 인증이 성공하면 성공 응답을 반환합니다.
        return Response({0}, status=status.HTTP_200_OK)


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        # Check if the login was successful
        if response.status_code == status.HTTP_200_OK:
            user = User.objects.get(email=request.data.get('email'))
            print("user: ", user)
            # Serialize user data to include in the response
            user_serializer = UserSerializer(user)
            print("user-ser: ", user_serializer)
            user_data = user_serializer.data

            # Extract token data from the response
            refresh = response.data.get('refresh')
            access = response.data.get('access')

            # Include user data and token information in the response
            response.data = {
                'user': user_data,
                'tokens': {
                    'refresh': refresh,
                    'access': access,
                }
            }

        return response
    

# class Java(TokenObtainPairView):
    

    
class GoogleLogin(APIView):
    """구글 소셜 로그인"""

    def get(self, request):
        return Response(GOOGLE_API_KEY, status=status.HTTP_200_OK)

    def post(self, request):
        access_token = request.data["access_token"]
        user_data = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_data = user_data.json()
        data = {
            "email": user_data.get("email"),
            "login_type": "google",
        }
        return SocialLogin(**data)




def SocialLogin(**kwargs):
    """소셜 로그인, 회원가입"""
    # 각각 소셜 로그인에서 email, nickname, login_type등을 받아옴!!
    data = {k: v for k, v in kwargs.items() if v is not None}
    # none인 값들은 빼줌
    email = data.get("email")
    login_type = data.get("login_type")
    # 그 중 email이 없으면 회원가입이 불가능하므로
    # 프론트에서 메시지를 띄워주고, 다시 로그인 페이지로 이동시키기
    if not email:
        return Response(
            {"error": "해당 계정에 email정보가 없습니다."}, status=status.HTTP_400_BAD_REQUEST
        )
    try:
        user = User.objects.get(email=email)
        # 로그인 타입까지 같으면, 토큰 발행해서 프론트로 보내주기
        if login_type == user.login_type:
            refresh = RefreshToken.for_user(user)
            access_token = CustomTokenObtainPairSerializer.get_token(user)
            return Response(
                {"refresh": str(refresh), "access": str(access_token.access_token)},
                status=status.HTTP_200_OK,
            )
        # 유저의 다른 소셜계정으로 로그인한 유저라면, 해당 로그인 타입을 보내줌.
        # (프론트에서 "{login_type}으로 로그인한 계정이 있습니다!" alert 띄워주기)
        else:
            return Response(
                {"error": f"{user.login_type}으로 이미 가입된 계정이 있습니다!"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    # 유저가 존재하지 않는다면 회원가입시키기
    except User.DoesNotExist:
        new_user = User.objects.create(**data)
        # pw는 사용불가로 지정
        new_user.set_unusable_password()
        new_user.save()
        # 이후 토큰 발급해서 프론트로
        refresh = RefreshToken.for_user(new_user)
        access_token = CustomTokenObtainPairSerializer.get_token(new_user)
        return Response(
            {"refresh": str(refresh), "access": str(access_token.access_token)},
            status=status.HTTP_200_OK,
        )