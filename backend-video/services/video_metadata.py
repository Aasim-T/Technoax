import cv2
import os

def get_video_metadata(video_path):

    cap = cv2.VideoCapture(video_path)

    fps = cap.get(cv2.CAP_PROP_FPS)

    total_frames = int(
        cap.get(cv2.CAP_PROP_FRAME_COUNT)
    )

    width = int(
        cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    )

    height = int(
        cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    )

    duration = 0

    if fps > 0:
        duration = total_frames / fps

    file_size = os.path.getsize(video_path)

    file_size_mb = round(
        file_size / (1024 * 1024),
        2
    )

    cap.release()

    return {
        "fps": round(fps, 2),
        "total_frames": total_frames,
        "duration_seconds": round(duration, 2),
        "resolution": f"{width}x{height}",
        "file_size_mb": file_size_mb
    }