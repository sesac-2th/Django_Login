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

# 장고 시크릿키
ENV SECRET_KEY=${SECRET_KEY}

# 데이터베이스
ENV DB_NAME=${DB_NAME}
ENV DB_USER=${DB_USER}
ENV DB_PASSWORD=${DB_PASSWORD}
ENV DB_HOST=${DB_HOST}
ENV DB_PORT=${DB_PORT}