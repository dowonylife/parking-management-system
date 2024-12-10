import easyocr
import cv2
import os

# EasyOCR Reader 생성
reader = easyocr.Reader(['ko', 'en'])  # 한국어, 영어, 숫자 인식

# 이미지 경로 및 결과 저장 경로 설정
img_path = '/home/dwlkb02/dowon/raspberrypi_parking-system/well/car_3.png'
output_dir = 'ocr_results'
os.makedirs(output_dir, exist_ok=True)

# 이미지 로드
img = cv2.imread(img_path)

# OCR 수행
result = reader.readtext(img_path)

# OCR 결과 임계값 설정
THRESHOLD = 0.5  # 신뢰도 임계값
filtered_results = []  # 신뢰도를 만족하는 결과 저장

# OCR 결과 필터링 및 이미지에 시각화
for bbox, text, conf in result:
    if conf > THRESHOLD:
        filtered_results.append((text, conf))
        # 텍스트와 박스 그리기
        cv2.rectangle(img, pt1=tuple(map(int, bbox[0])), pt2=tuple(map(int, bbox[2])), color=(0, 255, 0), thickness=3)
        cv2.putText(img, text, tuple(map(int, bbox[0])), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)

# 결과 저장
text_output_path = os.path.join(output_dir, 'recognized_texts.txt')
image_output_path = os.path.join(output_dir, 'annotated_image.jpg')

# 텍스트 결과 저장
with open(text_output_path, 'w') as f:
    for text, conf in filtered_results:
        f.write(f"차량 번호판: {text}, 신뢰도: {conf:.2f}\n")

# 결과 이미지 저장
cv2.imwrite(image_output_path, img)

print(f"OCR 결과가 저장되었습니다:\n텍스트 파일: {text_output_path}\n결과 이미지: {image_output_path}")
