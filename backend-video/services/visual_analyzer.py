import cv2
import numpy as np

def calculate_brightness(frame_path):

    image = cv2.imread(frame_path)

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    brightness = np.mean(gray)

    return brightness