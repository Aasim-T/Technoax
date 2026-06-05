ALLOWED_EXTENSIONS = [
    "mp4",
    "avi",
    "mov"
]

def validate_video(filename):

    extension = filename.split(".")[-1]

    return extension in ALLOWED_EXTENSIONS