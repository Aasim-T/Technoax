def generate_explanation(
    face_count,
    blur_score,
    brightness,
    deepfake_probability,
    risk_level
):

    reasons = []

    if deepfake_probability > 60:
        reasons.append(
            "elevated deepfake indicators detected"
        )

    if blur_score < 100:
        reasons.append(
            "low visual clarity observed"
        )

    if face_count == 0:
        reasons.append(
            "face detection inconsistency found"
        )

    if brightness < 50:
        reasons.append(
            "abnormally dark frames detected"
        )

    if len(reasons) == 0:
        reasons.append(
            "no significant anomalies detected"
        )

    return (
        f"Risk Level: {risk_level}. "
        + ", ".join(reasons)
        + "."
    )
    