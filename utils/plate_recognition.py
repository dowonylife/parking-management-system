import cv2
import numpy as np
import pytesseract
import re

pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

class PlateRecognition:
    def __init__(self, camera_index=-1, output_dir="./test_result"):
        self.camera = cv2.VideoCapture(camera_index)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 300)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 300)
        self.output_dir = output_dir

    def crop_image(self, img_box, rect, box, margin=10):
        """번호판 영역을 크롭"""
        Xs = [int(i[0]) for i in box]
        Ys = [int(i[1]) for i in box]
        x1, x2 = max(0, min(Xs) - margin), min(img_box.shape[1], max(Xs) + margin)
        y1, y2 = max(0, min(Ys) - margin), min(img_box.shape[0], max(Ys) + margin)
        return img_box[y1:y2, x1:x2]

    def correct_skew(self, image):
        """이미지 기울기 교정"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
        if lines is None:
            return image  # 기울기가 없으면 원본 반환
        angles = [(line[0][1] - np.pi / 2) * (180 / np.pi) for line in lines]
        avg_angle = np.mean(angles)
        center = (image.shape[1] // 2, image.shape[0] // 2)
        M = cv2.getRotationMatrix2D(center, avg_angle, 1.0)
        return cv2.warpAffine(image, M, (image.shape[1], image.shape[0]))

    def clean_plate_text(self, text):
        print(text)
        """번호판 텍스트 정리 및 유효성 확인"""
        cleaned_text = re.sub(r'[^\uAC00-\uD7A3\d]', '', text)  # 한글과 숫자만 유지
        if len(cleaned_text) >= 6 and len(cleaned_text) <= 10:
            return cleaned_text
        return None

    def process_saved_frame(self, frame):
        """프레임에서 번호판 탐지 및 OCR 수행"""
        frame = self.correct_skew(frame)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        value_channel = cv2.split(hsv)[2]  # HSV 값 채널 사용
        thresh = cv2.adaptiveThreshold(cv2.GaussianBlur(value_channel, (5, 5), 0), 
                                       255, 
                                       cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY_INV, 
                                       19, 9)
        contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        results = []

        for contour in contours:
            if cv2.contourArea(contour) < 1000:
                continue  # 너무 작은 영역 무시
            rect = cv2.minAreaRect(contour)
            box = cv2.boxPoints(rect)
            box = np.int64(box)
            cropped = self.crop_image(value_channel, rect, box)
            if cropped is None or cropped.size == 0:
                continue
            gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY) if len(cropped.shape) == 3 else cropped

            # 다양한 임계값으로 OCR 수행
            for threshold in [150, 170, 190, 210]:
                _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
                text = pytesseract.image_to_string(binary, config='--oem 3 --psm 7', lang='kor').strip()
                cleaned_text = self.clean_plate_text(text)
                if cleaned_text:
                    results.append(cleaned_text)

        return list(set(results))  # 중복 제거 후 반환

    def capture_plate(self):
        """카메라에서 프레임 캡처 후 번호판 인식"""
        success, frame = self.camera.read()
        if success:
            return self.process_saved_frame(frame)
        return []
    
    def gen_frames(self):
        """카메라 프레임 스트림 생성"""
        while True:
            success, frame = self.camera.read()
            if not success:
                break
            else:
                _, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                      b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
