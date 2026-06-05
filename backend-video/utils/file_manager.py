import os

UPLOAD_DIR = "uploads/videos"

os.makedirs(UPLOAD_DIR, exist_ok=True)

async def save_uploaded_file(file):

    file_path = os.path.join(
        UPLOAD_DIR,
        file.filename
    )

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    return file_path