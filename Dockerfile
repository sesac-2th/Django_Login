FROM python:3.11

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 작업 디렉터리 설정
WORKDIR /app

# 의존성 설치
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# 소스 코드 복사
COPY . /app/

# Gunicorn 실행
CMD ["gunicorn", "login.wsgi:application", "-b", "0.0.0.0:8000"]
