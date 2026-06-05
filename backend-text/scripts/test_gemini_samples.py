"""
Manual integration test for Technoax hybrid Gemini scoring.

Run from backend/:
    python scripts/test_gemini_samples.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

SAMPLES = {
    "neutral": "The city council approved new transportation improvements.",
    "manipulative": (
        "URGENT! Doctors don't want you to know this shocking secret cure!"
    ),
    "llm_style": (
        "This revolutionary innovation represents a transformative advancement that "
        "significantly enhances operational efficiency across multiple domains."
    ),
}


def run_sample(label: str, text: str) -> None:
    client = TestClient(app)
    response = client.post("/analyze-text", json={"text": text})
    print(f"\n=== {label.upper()} ===")
    print("Status:", response.status_code)
    if response.status_code != 200:
        print(response.text)
        return

    data = response.json()
    print("Trust Score:", data["trust_score"])
    print("Trust Meter:", data["trust_meter"])
    print("Risk Level:", data["risk_level"])
    print("Patterns:", data["detected_patterns"])
    print("Matched Words:", len(data["matched_words"]))
    print("Heatmap Entries:", len(data["manipulation_heatmap"]))
    print("AI Explanation:", data["ai_explanation"][:200], "...")
    print("Recommendation:", data["recommendation"][:120], "...")
    print("AI Generated Probability:", data.get("ai_generated_probability"))
    print("AI Generation Explanation:", data.get("ai_generation_explanation", "")[:200], "...")


if __name__ == "__main__":
    for name, content in SAMPLES.items():
        run_sample(name, content)
