import cv2

CASCADE_PATH = cv2.data.haarcascades + \
    "haarcascade_frontalface_default.xml"

face_cascade = cv2.CascadeClassifier(
    CASCADE_PATH
)

def detect_faces(frame_path):

    image = cv2.imread(frame_path)

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )

    return len(faces)