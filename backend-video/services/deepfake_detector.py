import random

def detect_deepfake(frame_path):

    score = random.randint(20, 80)

    return {
        "deepfake_probability": score
    }