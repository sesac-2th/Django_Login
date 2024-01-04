from django.contrib.auth import authenticate
from django.http import JsonResponse
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from users.serializers import UserSerializer, CustomTokenObtainPairSerializer
from users.models import User
from django.contrib.auth.hashers import make_password
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import User
from .serializers import UserSerializer
import base64, json
import os
import requests
import boto3
import time
from botocore.exceptions import NoCredentialsError
from requests_toolbelt.multipart.encoder import MultipartEncoder
from dotenv import load_dotenv
from django.core.cache import cache
import json
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
load_dotenv()

class SignUpView(APIView):
    permission_classes = (permissions.AllowAny,)
    @swagger_auto_schema(
        request_body=UserSerializer,
        responses={201: UserSerializer}
    )

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        password2 = request.data.get("password2")  # 2차 비밀번호 입력
        gender = request.data.get("gender")  # 성별 입력

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


        # 비밀번호를 해싱하여 저장
        user = User.objects.create(email=email, gender=gender)
        user.set_password(password)
        user.save()
        
        # 사용자 정보를 시리얼라이즈하고 응답에 gender 포함
        serializer = UserSerializer(user)
        response_data = serializer.data
        response_data['gender'] = gender

        serializer = UserSerializer(user)
        return Response(response_data, status=status.HTTP_201_CREATED)

    
class AuthCheck(APIView):
    # authentication_classes = [JSONWebTokenAuthentication]
    # permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                type=openapi.TYPE_STRING,
                description='Bearer token for authentication',
                required=True,
            ),
        ],
        responses={
            200: openapi.Response(
                description="Authentication successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Authentication successful'),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='0'),
                    },
                ),
            ),
            401: "Unauthorized",
        },
    )

    def get(self, request):
        # 여기에서는 별다른 로직을 추가하여 인증을 확인하거나 처리합니다.
        # 이 예제에서는 인증이 성공하면 성공 응답을 반환합니다.
        return Response(0, status=status.HTTP_200_OK)


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

class GenerateVideoView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'image': openapi.Schema(type=openapi.TYPE_FILE, description='Image file (JPEG or PNG)'),
            },
            required=['image'],
        ),
        responses={
            200: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'video_id': openapi.Schema(type=openapi.TYPE_STRING, description='Generated video ID')}),
            400: "Bad Request",
            500: "Internal Server Error",
        },
    )
    def post(self, request):
        engine_id = "stable-diffusion-xl-1024-v1-0"
        api_host = os.getenv('API_HOST')
        api_key = os.getenv('STABILITY_API_KEY')
        
        if api_key is None:
            return JsonResponse({"error": "Missing Stability API key."}, status=status.HTTP_400_BAD_REQUEST)

        image_file = request.FILES.get('image')

        if not image_file:
            return JsonResponse({"error": "Image file is required."}, status=status.HTTP_400_BAD_REQUEST)

        seed = request.data.get("seed", 0)
        cfg_scale = request.data.get("cfg_scale", 2.5)
        motion_bucket_id = request.data.get("motion_bucket_id", 40)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "multipart/form-data"
        }

        allowed_image_formats = ['image/jpeg', 'image/png']

        image_content_type = image_file.content_type
        if image_content_type not in allowed_image_formats:
            return JsonResponse({"error": "Only JPEG or PNG images are allowed."}, status=status.HTTP_400_BAD_REQUEST)

        payload = MultipartEncoder(
            fields={
                'image': (image_file.name, image_file.read(), image_content_type),
                'seed': str(seed),
                'cfg_scale': str(cfg_scale),
                'motion_bucket_id': str(motion_bucket_id),
            }
        )
        
        headers['Content-Type'] = payload.content_type

        response = requests.post(
            f"{api_host}/v2alpha/generation/image-to-video",
            headers=headers,
            data=payload
        )
        print(response.json())
        
        if response.status_code == 400:
            error_data = response.json()
            error_name = error_data.get("name", "Unknown error")
            errors = error_data.get("errors", ["Unknown error occurred."])

            error_message = f"{error_name}: {', '.join(errors)}"

            return JsonResponse({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        elif response.status_code == 500:
            error_data = response.json()
            error_name = error_data.get("name", "Unknown error")
            errors = error_data.get("errors", ["Unknown error occurred."])

            error_message = f"{error_name}: {', '.join(errors)}"
            return JsonResponse({"error": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        elif response.status_code != 200:
            return JsonResponse({"error": "Non-200 response: " + str(response.text)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        data = response.json()
        video_id = data.get("id")
        
        time.sleep(60)
        # S3에 동영상 저장
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }
        
        url = f"{api_host}/v2alpha/generation/image-to-video/result/{video_id}"

        try:
            response = requests.get(url, headers=headers)
            print("statusCode: ", response.raise_for_status())

            content = response.json()
            print("content: ", content)
            video_content_base64 = content['video'] #response.json().get('video', '')        
            video_content = base64.b64decode(video_content_base64)
            s3_bucket_name = os.getenv('BUCKET_NAME')
            s3_access_key = os.getenv('BUCKET_ACCESS_KEY')
            s3_secret_key = os.getenv('BUCKET_SECRET_KEY')
            s3_key = f"videos/{request.user.pk}/{video_id}.mp4"

            s3_client = boto3.client('s3', aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key)
            s3_client.put_object(Body=video_content, Bucket=s3_bucket_name, Key=s3_key, ContentType="video/mp4")

            s3_video_url = f"https://{s3_bucket_name}.s3.amazonaws.com/{s3_key}"
            
            user = request.user
            user_id = user.id
            
            s3_key_video = f"videos/{user_id}"
            s3_video_url = f"https://{s3_bucket_name}.s3.amazonaws.com/{s3_key_video}"
            print(s3_video_url)
            # S3 클라이언트 생성
            s3_client = boto3.client('s3', aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key)

            response = s3_client.list_objects(Bucket=s3_bucket_name, Prefix=s3_key_video)
            objects = response.get('Contents', [])
            
            # 파일 목록 생성
            file_list = [f"{s3_video_url}/{f['Key'][len(s3_key_video)+1:]}" for f in objects]
            # cache.set(user_id, json.dumps(file_list), 300)
            jsonObj = {"s3_video_url": s3_video_url, "file_list": file_list}
            cache.set(user_id, json.dumps(jsonObj), 60*60*12)
            return JsonResponse({"video_id": video_id, "s3_video_url": s3_video_url}, status=status.HTTP_200_OK)
        
        except requests.exceptions.RequestException as e:
            return JsonResponse({"error": f"Failed to download video: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                type=openapi.TYPE_STRING,
                description='Bearer token for authentication',
                required=True,
            ),
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'cloudfront_url': openapi.Schema(type=openapi.TYPE_STRING, description='CloudFront URL for videos'),
                    'file_list': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                },
            ),
            500: "Internal Server Error",
        },
    )
    def get(self, request):
        # 사용자 정보 가져오기
        user = request.user
        user_id = user.id
        print(user)
        print(user_id)
        # 동영상 경로 조회
        s3_bucket_name = os.getenv('BUCKET_NAME')
        s3_access_key = os.getenv('BUCKET_ACCESS_KEY')
        s3_secret_key = os.getenv('BUCKET_SECRET_KEY')
        s3_key_video = f"videos/{user_id}"
        s3_video_url = f"https://{s3_bucket_name}.s3.amazonaws.com/{s3_key_video}"
        print(s3_video_url)
        
        # cdn url 치환
        cloudfront_url = "https://d1zjfdzmtf1vra.cloudfront.net"
        file_list = []
        
        # S3 클라이언트 생성
        s3_client = boto3.client('s3', aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key)

        # S3 객체 목록 가져오기
        try:
            videoUrls = cache.get(user_id)
            if videoUrls:
                print("redis cache hit")
                print("videoUrls: ", videoUrls)
                return JsonResponse(json.loads(videoUrls), status=status.HTTP_200_OK)
            response = s3_client.list_objects(Bucket=s3_bucket_name, Prefix=s3_key_video)
            objects = response.get('Contents', [])
            
            # 파일 목록 생성
            # file_list = [f"{s3_video_url}/{f['Key'][len(s3_key_video)+1:]}" for f in objects]
            # return JsonResponse({"s3_video_url": s3_video_url, "file_list": file_list}, status=status.HTTP_200_OK)
            
            for f in objects:
                s3_object_key = f['Key'][len(s3_key_video) + 1:]
                cloudfront_object_url = f"{cloudfront_url}/videos/{user_id}/{s3_object_key}"
                file_list.append(cloudfront_object_url)

            return JsonResponse({"cloudfront_url": cloudfront_url, "file_list": file_list}, status=status.HTTP_200_OK)

        except Exception as e:
            return JsonResponse({"error": f"Failed to retrieve file list from S3: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  