import cv2
import numpy as np
from PIL import Image
import io

# Load OpenCV's pre-trained Haar Cascade face detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def contains_face(image_data):
    """
    Checks if an image contains a face using OpenCV Haar Cascade.
    """
    try:
        img = Image.open(io.BytesIO(image_data)).convert('RGB')
        img_array = np.array(img)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

        return len(faces) > 0
    except Exception as e:
        print(f"Error processing image: {e}")
        return False
