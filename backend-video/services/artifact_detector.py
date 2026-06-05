import cv2

def detect_blur(frame_path):

    image = cv2.imread(frame_path)

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    score = cv2.Laplacian(
        gray,
        cv2.CV_64F
    ).var()

    return score