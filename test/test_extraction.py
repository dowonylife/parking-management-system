import cv2
import numpy as np
import argparse
import pytesseract
import os
import re
from PIL import Image

# 결과 저장 디렉터리 설정
output_dir = "./test_result"
os.makedirs(output_dir, exist_ok=True)

# 번호판 크롭 함수
def crop_image(img_box, rect, box, margin=10):
    # box의 x, y 좌표에서 최소와 최대값 계산
    Xs = [int(i[0]) for i in box]
    Ys = [int(i[1]) for i in box]
    x1, x2 = min(Xs), max(Xs)  # x 범위
    y1, y2 = min(Ys), max(Ys)  # y 범위

    # 여유값 추가
    x1 = max(0, x1 - margin)  # 이미지 경계를 초과하지 않도록 max 사용
    y1 = max(0, y1 - margin)
    x2 = min(img_box.shape[1], x2 + margin)  # 이미지 크기를 초과하지 않도록 min 사용
    y2 = min(img_box.shape[0], y2 + margin)

    # 바운딩 박스 크롭
    cropped = img_box[y1:y2, x1:x2]

    return cropped

def correct_skew(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150, apertureSize=3)

    # Hough Line Transform을 사용하여 선 탐지
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
    angles = []

    # 기울기 계산
    for line in lines:
        rho, theta = line[0]
        angle = (theta - np.pi / 2) * (180 / np.pi)
        angles.append(angle)

    # 평균 기울기로 정렬
    avg_angle = np.mean(angles)
    center = (image.shape[1] // 2, image.shape[0] // 2)
    M = cv2.getRotationMatrix2D(center, avg_angle, 1.0)
    rotated = cv2.warpAffine(image, M, (image.shape[1], image.shape[0]))

    return rotated

# OCR 결과 저장 함수
def save_text(output_dir, filename, text):
    text_file_path = os.path.join(output_dir, "extracted_text.txt")
    with open(text_file_path, "a", encoding="utf-8") as f:
        f.write(f"Image: {filename}\n{text}\n")

# 번호판 텍스트 클리닝 및 필터링 함수
def clean_and_validate_plate(text):
    # 텍스트 정리: 한글과 숫자만 남기기
    cleaned_text = re.sub(r'[^\uAC00-\uD7A3\d]', '', text)

    # 한글과 숫자 검증: 한글이 1글자 이상 포함되어야 함
    korean_characters = re.findall(r'[\uAC00-\uD7A3]', cleaned_text)
    if len(korean_characters) != 1:  # 한글이 정확히 1글자여야 함
        return None

    # 길이 검증
    if 6 <= len(cleaned_text) <= 10:
        return cleaned_text

    return None

# 메인 코드
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", type=str, required=True, help="path to input image")
args = vars(ap.parse_args())

# 입력 이미지 로드
img = cv2.imread(args["image"])
rotatedImg = correct_skew(img)

hsv = cv2.cvtColor(rotatedImg, cv2.COLOR_BGR2HSV)
hue, saturation, value = cv2.split(hsv)

# 전처리
blur = cv2.GaussianBlur(value, (5, 5), 0)
thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 19, 9)

# 윤곽선 검출
contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

# 이미지 크기 확인
height, width = thresh.shape
imageContours = np.zeros((height, width, 3), dtype=np.uint8)

# 번호판 탐지 및 OCR 처리
for i, contour in enumerate(contours):
    if cv2.contourArea(contour) < 1000:
        continue

    x, y, w, h = cv2.boundingRect(contour)
    ratio = w / h

    # 번호판 조건 필터링
    if not (1.5 < ratio < 5.0):
        continue

    rect = cv2.minAreaRect(contour)
    box = cv2.boxPoints(rect)
    box = np.int64(box)

    cv2.drawContours(imageContours, [box], 0, (0, 255, 0), 2)

    # 번호판 크롭
    cropped = crop_image(value, rect, box)
    filename = f"plate_{i}.png"
    filepath = os.path.join(output_dir, filename)
    cv2.imwrite(filepath, cropped)

    # 예외처리
    if cropped is None or cropped.size == 0:
        raise ValueError("Cropped image is empty or invalid.")
    
    # 전처리
    if len(cropped.shape) == 2:  # 이미 흑백 이미지인 경우
        gray = cropped
    elif len(cropped.shape) == 3:  # BGR 이미지인 경우
        gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    else:
        raise ValueError("Invalid image format: cropped image has unexpected dimensions.")
    
    # 이진화
    _, binary = cv2.threshold(gray, 190, 255, cv2.THRESH_BINARY)
    denoised = cv2.medianBlur(binary, 3)  # 노이즈 제거
    filename = f"gray_plate_{i}.png"
    
    filepath = os.path.join(output_dir, filename)
    cv2.imwrite(filepath, denoised)

    # OCR 처리
    custom_config = r'--oem 3 --psm 7'  # LSTM 엔진, 단일 라인 텍스트 처리
    ocr_text = pytesseract.image_to_string(denoised, config=custom_config, lang='kor').strip()
    cleaned_text = clean_and_validate_plate(ocr_text)
    if cleaned_text:
        save_text(output_dir, filename, cleaned_text)
        print(f"Valid Plate Found: {filename}, Text: {cleaned_text}")

# 윤곽선 이미지 저장
contour_image_path = os.path.join(output_dir, "contours.png")
cv2.imwrite(contour_image_path, imageContours)
print(f"Saved contours image: {contour_image_path}")
