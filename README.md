# Parking Management System

A smart parking management system implemented using Raspberry Pi, integrating various hardware (LEDs, FND, Servo Motor, and Camera) and software (OCR and Flask web framework) to manage vehicle entry and exit efficiently.

## Features

- **License Plate Recognition (OCR):**
  Automatically detects and processes vehicle license plates for entry and exit using a camera.
  
- **Visual and Audio Feedback:**
  Utilizes RGB LEDs and a buzzer to provide real-time feedback to users:
  - **Red LED**: Blinks during vehicle entry.
  - **Blue LED**: Lights up during license plate recognition.
  - **Green LED**: Lights up when recognition is successful.
  - **Buzzer**: Provides sound alerts during critical actions.

- **Automatic Barrier Control:**
  Controls a servo motor to open and close the barrier during vehicle entry and exit.

- **Real-time Display:**
  Displays the last four digits of the vehicle's license plate on an FND (7-segment display).

- **Blacklist Management:**
  Blocks specific vehicles from entering the parking lot.

- **Web-based Management Interface:**
  - View and manage current parking status and available spots.
  - Add or remove vehicles from the blacklist.
  - Generate monthly parking statistics and revenue reports.

- **Monthly Statistics and Reports:**
  Visualize data using graphs to analyze entry, exit, and revenue trends.

- **GPIO Resource Management:**
  Safely cleans up GPIO resources on shutdown.

---

## Hardware Requirements

1. **Raspberry Pi 4B**
2. **Camera Module**
3. **RGB LEDs**
4. **Buzzer**
5. **Servo Motor**
6. **FND (7-Segment Display)**
7. **Wires and Breadboard**

---

## Software Setup

### Prerequisites

- Install Python 3.9 or higher.
- Ensure `pip` is installed.

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/dowonylife/parking-management-system.git
   cd parking-management-system
### Prerequisites and Setup for License Plate Recognition

To enable license plate recognition using Tesseract OCR and OpenCV on Raspberry Pi, follow these steps:

1. **Install Required Libraries:**

    Install Tesseract OCR and its language data files for Korean (or your desired language):

    ```bash
    sudo apt-get update
    sudo apt-get install tesseract-ocr
    sudo apt-get install tesseract-ocr-kor
    ```

    Install essential Python libraries for image processing and OCR:

    ```bash
    pip install opencv-python
    pip install pytesseract
    pip install numpy
    pip install matplotlib
    ```

2. **Configure Tesseract OCR Path:**

    If Tesseract OCR is not found automatically, specify its path in your Python script:

    ```python
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
    ```

3. **Configure GPIO and Camera:**

    Use the `raspi-config` utility to enable necessary hardware interfaces:

    ```bash
    sudo raspi-config
    ```

    - Navigate to **Interfacing Options** > **Camera** and enable the camera module.
    - Enable SPI and I2C interfaces for GPIO functionality.

4. **Test Camera Functionality:**

    Verify that the Raspberry Pi camera is functioning correctly using:

    ```bash
    raspistill -o test.jpg
    ```

    Check if the image is saved successfully.

5. **Install OpenCV Dependencies:**

    OpenCV may require additional system-level libraries. Install them using:

    ```bash
    sudo apt-get install libhdf5-dev libhdf5-serial-dev libhdf5-103
    sudo apt-get install libqtgui4 libqtwebkit4 libqt4-test python3-pyqt5
    sudo apt-get install libatlas-base-dev libjasper-dev libilmbase23 libopenexr23 libgstreamer1.0-dev
    ```

6. **Verify Installation:**

    Test OCR functionality with a sample image:

    ```python
    import cv2
    import pytesseract

    image = cv2.imread('sample_license_plate.jpg')
    text = pytesseract.image_to_string(image, lang='kor')
    print("Extracted Text:", text)
    ```
