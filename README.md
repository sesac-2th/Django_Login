## 🔑 프로젝트 설치 및 실행 방법
#### 깃허브 클론하기
```bash
$ git init
$ git clone <레파지토리 주소>
```
#### 패키지 밎 라이브러리 설치 | https://python-poetry.org/docs/
```bash
$ poetry shell
$ poetry install
```


#### 가상환경 실행 후 django 프로젝트 실행
```bash
$ python manage.py makemigrations | 마이그레이션
$ python manage.py migrate | 마이그레이트
$ python manage.py createsuperuser | 관리자 계정생성
$ python manage.py runserver | 로컬서버 실행
```
