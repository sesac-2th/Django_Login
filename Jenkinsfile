pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: kaniko
    image: gcr.io/kaniko-project/executor:debug
    command:
    - sleep
    args:
    - infinity
    volumeMounts:
    - name: kaniko-secret
      mountPath: /kaniko/.docker
  volumes:
  - name: kaniko-secret
    secret:
      secretName: regcred
      items:
      - key: .dockerconfigjson
        path: config.json
'''
        }
    }

    environment {
        dockerHubRegistry = 'woongpang/django-login2'
        dockerHubRegistryCredential = 'dockerhub-woongpang'
        pythonVersion = '3.11'
        SLACK_CHANNEL = '#팀프로젝트-2조'
        SLACK_SUCCESS_COLOR = '#2C953C'
        SLACK_FAIL_COLOR = '#FF3232'
    }
    stages {
        stage('Git 브랜치 체크아웃') {
            steps {
                script {
                    dir("${WORKSPACE}") {
                        sh 'rm -rf *'
                        sh 'git init'
                        sh 'git remote add origin https://github.com/sesac-2th/Django_Login_BE.git'
                        sh 'git fetch --tags --progress https://github.com/sesac-2th/Django_Login_BE.git +refs/heads/*:refs/remotes/origin/*'
                        sh 'git checkout -b main --track origin/main'
                    }
                }
            }
            post {
                failure {
                    echo 'Repository clone 실패 !'
                    slackSend (
                        channel: SLACK_CHANNEL,
                        message: "${env.JOB_NAME}(${env.BUILD_NUMBER})의 Repository clone이 실패하였습니다."
                    )
                }
                success {
                    echo 'Repository clone 성공 !'
                    slackSend (
                        channel: SLACK_CHANNEL,
                        message: "${env.JOB_NAME}(${env.BUILD_NUMBER})의 Repository clone이 성공하였습니다."
                    )
                }
            }
        }

        stage('Dockerfile 확인') {
            steps {
                script {
                    dir("${WORKSPACE}") {
                        sh 'ls -la'
                        sh 'cat Dockerfile'
                    }
                }
            }
        }

        stage('Docker 이미지 빌드 & 태깅 & 푸시') {
            steps {
                container('kaniko') {
                    // kaniko를 사용하여 Docker 이미지 빌드
                    sh "/kaniko/executor --dockerfile Dockerfile --context dir:///${WORKSPACE} --destination=${dockerHubRegistry}:${currentBuild.number}"
                }
            }
            post {
                failure {
                    echo 'Docker 이미지 빌드 실패 !'
                    slackSend (
                        channel: SLACK_CHANNEL,
                        color: SLACK_FAIL_COLOR,
                        message: "${env.JOB_NAME}(${env.BUILD_NUMBER})의 Docker 이미지 빌드가 실패하였습니다."
                    )
                }
                success {
                    echo 'Docker 이미지 빌드 성공 !'
                    slackSend (
                        channel: SLACK_CHANNEL,
                        color: SLACK_SUCCESS_COLOR,
                        message: "${env.JOB_NAME}(${env.BUILD_NUMBER})의 Docker 이미지 빌드가 성공하였습니다."
                    )
                }
            }
        }

        stage('K8S Manifest 업데이트') {
            steps {
                script {
                    // git 레포지토리 초기화
                    sh 'mkdir ../Argo'
                    sh 'cd ../Argo && git init'

                    // git 구성
                    sh 'cd ../Argo && git config user.email "jr.woong@gmail.com"'
                    sh 'cd ../Argo && git config user.name "woongpang"'

                    // 레포지토리 클론 및 메인 브랜치로 전환
                    sh 'cd ../Argo && git remote add origin https://github.com/sesac-2th/k8s-manifest.git'
                    sh 'cd ../Argo && git fetch --tags --progress https://github.com/sesac-2th/k8s-manifest.git +refs/heads/*:refs/remotes/origin/*'
                    sh 'cd ../Argo && git checkout -t origin/main'

                    // 수정 전 deployment.yaml 내용 표시
                    sh 'cd ../Argo && cat deployment.yaml'

                    // deployment.yaml에서 이미지 버전 변경
                    sh "cd ../Argo && sed -i 's+woongpang/django-login2.*+woongpang/django-login2:${currentBuild.number}+g' deployment.yaml"

                    // 수정 후 deployment.yaml 내용 표시
                    sh 'cd ../Argo && cat deployment.yaml'

                    // 변경 내용 추가 및 커밋
                    sh 'cd ../Argo && git add .'
                    sh "cd ../Argo && git commit -m '[UPDATE] my-django-app ${currentBuild.number} 이미지 버전 업데이트'"

                    // 자격 증명을 사용하여 변경 내용 푸시
                    withCredentials([usernamePassword(credentialsId: 'github-woongpang', passwordVariable: 'GIT_PASSWORD', usernameVariable: 'GIT_USERNAME')]) {
                        sh "cd ../Argo && git push https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/sesac-2th/k8s-manifest.git HEAD:main"
                    }
                }
            }
            post {
                failure {
                    echo 'K8S Manifest 업데이트 실패 !'
                    slackSend (
                        channel: SLACK_CHANNEL,
                        color: SLACK_FAIL_COLOR,
                        message: "${env.JOB_NAME}(${env.BUILD_NUMBER})의 K8S Manifest 업데이트가 실패하였습니다."
                    )
                }
                success {
                    echo 'K8S Manifest 업데이트 성공 !'
                    slackSend (
                        channel: SLACK_CHANNEL,
                        color: SLACK_SUCCESS_COLOR,
                        message: "${env.JOB_NAME}(${env.BUILD_NUMBER})의 K8S Manifest 업데이트가 성공하였습니다."
                    )
                }
            }
        }
    }
}