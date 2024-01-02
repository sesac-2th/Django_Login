import json
import base64

def decode_and_save_video(json_file_path, output_file_path):
    # JSON 파일 열기
    with open(json_file_path, 'r') as json_file:
        # JSON 데이터 로드
        data = json.load(json_file)

        # video 필드에서 Base64 디코딩
        video_data = base64.b64decode(data.get('video'))

        # MP4 파일로 저장
        with open(output_file_path, 'wb') as output_file:
            output_file.write(video_data)

if __name__ == "__main__":
    json_video_file_path = "/Users/juhwanlee/Desktop/project/login/test.txt"
    output_file_name_and_path = "output_video.mp4"

    decode_and_save_video(json_video_file_path, output_file_name_and_path)
    print(f"동영상이 {output_file_name_and_path} 파일로 성공적으로 저장되었습니다.")