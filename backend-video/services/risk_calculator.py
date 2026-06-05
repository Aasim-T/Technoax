def calculate_risk_score(
    face_count,
    blur_score,
    brightness,
    deepfake_probability
):

    score = 0

    score += deepfake_probability * 0.6

    if blur_score < 100:
        score += 15

    if face_count == 0:
        score += 10

    if brightness < 50:
        score += 5

    score = min(round(score), 100)

    if score < 40:
        level = "Low"
    elif score < 70:
        level = "Medium"
    else:
        level = "High"

    return {
        "risk_score": score,
        "risk_level": level
    }