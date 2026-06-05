"""Versioned prompt template framework for structured Gemini interactions.

Provides a registry of versioned, anti-hallucination prompt templates
with consistent JSON enforcement across all Gemini API calls.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from models.response_models import MatchedWord

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PromptTemplate:
    """A versioned prompt template with metadata."""

    name: str
    version: str
    description: str
    system_instruction: str
    user_template: str
    max_input_chars: int = 8000


class PromptRegistry:
    """
    Singleton registry of versioned prompt templates for Gemini.

    Provides consistent anti-hallucination guardrails, JSON schema enforcement,
    and deterministic output formatting across all Gemini calls.
    """

    _instance: "PromptRegistry | None" = None

    def __new__(cls) -> "PromptRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._templates = {}
            cls._instance._register_defaults()
        return cls._instance

    def _register_defaults(self) -> None:
        """Register all built-in prompt templates."""
        self.register(self._trust_analysis_v2())
        self.register(self._ai_authenticity_v2())
        self.register(self._deep_explainability_v1())
        self.register(self._social_engineering_v1())
        self.register(self._contextual_risk_v1())

    def register(self, template: PromptTemplate) -> None:
        """Register a prompt template by name."""
        key = f"{template.name}:{template.version}"
        self._templates[key] = template
        logger.debug("Registered prompt template: %s", key)

    def get(self, name: str, version: str | None = None) -> PromptTemplate:
        """
        Retrieve a prompt template by name and optional version.

        If no version is specified, returns the latest registered version.
        """
        if version:
            key = f"{name}:{version}"
            if key in self._templates:
                return self._templates[key]
            raise KeyError(f"Prompt template not found: {key}")

        # Find latest version of this template
        candidates = {
            k: v for k, v in self._templates.items()
            if k.startswith(f"{name}:")
        }
        if not candidates:
            raise KeyError(f"No prompt templates found for: {name}")

        return max(candidates.values(), key=lambda t: t.version)

    def render(self, name: str, version: str | None = None, **kwargs: Any) -> str:
        """
        Render a prompt template with the given variables.

        The template's system_instruction and user_template are concatenated,
        with user_template formatted using kwargs.
        """
        template = self.get(name, version)

        # Truncate text content to max_input_chars
        if "text" in kwargs and len(kwargs["text"]) > template.max_input_chars:
            kwargs["text"] = kwargs["text"][:template.max_input_chars]

        # Format matched_words if present
        if "matched_words" in kwargs and isinstance(kwargs["matched_words"], list):
            if kwargs["matched_words"] and hasattr(kwargs["matched_words"][0], "model_dump"):
                kwargs["matched_words_json"] = json.dumps(
                    [w.model_dump() for w in kwargs["matched_words"]],
                    ensure_ascii=False,
                )
            else:
                kwargs["matched_words_json"] = json.dumps(kwargs["matched_words"], ensure_ascii=False)

        user_content = template.user_template.format(**kwargs)
        return f"{template.system_instruction}\n\n{user_content}"

    def list_templates(self) -> list[dict[str, str]]:
        """List all registered templates with metadata."""
        return [
            {
                "name": t.name,
                "version": t.version,
                "description": t.description,
            }
            for t in self._templates.values()
        ]

    # ── Built-in Templates ──────────────────────────────────────────────

    @staticmethod
    def _trust_analysis_v2() -> PromptTemplate:
        return PromptTemplate(
            name="trust_analysis",
            version="v2",
            description="Enhanced contextual trust analysis with domain awareness",
            system_instruction=(
                "You are Technoax, an explainable digital trust intelligence system. "
                "You analyze content for trustworthiness with precision and evidence-based reasoning. "
                "RULES: "
                "1) Return ONLY valid JSON — no markdown, no commentary. "
                "2) Base scores on concrete evidence in the text, not assumptions. "
                "3) Do NOT hallucinate patterns that are not present. "
                "4) Be calibrated: neutral factual content should score 75-95. "
                "5) Only highly manipulative content should score below 30."
            ),
            user_template=(
                "Analyze the following content for trustworthiness.\n\n"
                "Domain context: {domain}\n\n"
                "Evaluate these specific dimensions:\n"
                "- Emotional manipulation intensity (fear, guilt, anger exploitation)\n"
                "- Urgency/pressure tactics (artificial time pressure, scarcity claims)\n"
                "- Clickbait/sensationalism (exaggerated claims, misleading hooks)\n"
                "- Conspiracy framing (anti-establishment rhetoric, hidden truth claims)\n"
                "- Social engineering (authority impersonation, reciprocity pressure)\n"
                "- Factual grounding (verifiable claims vs. unsubstantiated assertions)\n\n"
                "Return JSON:\n"
                '{{\n'
                '  "trust_score": integer (0-100),\n'
                '  "explanation": "string — concise evidence-based rationale",\n'
                '  "recommendation": "string — actionable verification guidance"\n'
                '}}\n\n'
                'Content:\n"""\n{text}\n"""'
            ),
        )

    @staticmethod
    def _ai_authenticity_v2() -> PromptTemplate:
        return PromptTemplate(
            name="ai_authenticity",
            version="v2",
            description="Enhanced AI-generation detection with multi-signal prompting",
            system_instruction=(
                "You are Technoax AI-authenticity engine specializing in distinguishing "
                "human-written from AI-generated content. "
                "RULES: "
                "1) Return ONLY valid JSON. "
                "2) Analyze concrete linguistic features, not content topic. "
                "3) Consider: sentence structure variance, vocabulary diversity, "
                "idiomatic expressions, personal voice, typos/colloquialisms. "
                "4) LLM outputs tend to be: overly structured, consistently formal, "
                "lacking personal anecdotes, using hedge phrases excessively. "
                "5) Do NOT assume all polished text is AI-generated."
            ),
            user_template=(
                "Analyze whether this content appears AI-generated.\n\n"
                "Statistical pre-analysis signals:\n"
                "- Burstiness score: {burstiness_score}/100\n"
                "- Vocabulary richness: {vocabulary_score}/100\n"
                "- Formality index: {formality_score}/100\n\n"
                "Your analysis should complement (not contradict) these statistical signals "
                "unless you have strong evidence to diverge.\n\n"
                "Return JSON:\n"
                '{{\n'
                '  "ai_generated_probability": integer (0-100),\n'
                '  "ai_generation_explanation": "string — evidence-based linguistic analysis"\n'
                '}}\n\n'
                'Content:\n"""\n{text}\n"""'
            ),
        )

    @staticmethod
    def _deep_explainability_v1() -> PromptTemplate:
        return PromptTemplate(
            name="deep_explainability",
            version="v1",
            description="Deep reasoning chain for trust explanation",
            system_instruction=(
                "You are Technoax, a senior explainable digital trust intelligence analyst. "
                "You produce professional trust briefings with evidence-based reasoning. "
                "RULES: "
                "1) Return ONLY valid JSON. "
                "2) Reference specific detected patterns as evidence. "
                "3) Explain psychological manipulation mechanisms when present. "
                "4) Avoid: 'As an AI', 'In conclusion', 'It's important to note'. "
                "5) Be concise, professional, and evidence-oriented."
            ),
            user_template=(
                "Produce a professional trust briefing for the content below.\n\n"
                "Rule-based intelligence (authoritative — do not contradict):\n"
                "- Hybrid trust score: {trust_score}/100\n"
                "- Trust meter: {trust_meter}\n"
                "- Risk level: {risk_level}\n"
                "- Domain context: {domain}\n"
                "- Detected categories: {patterns}\n"
                "- Matched signals: {matched_words_json}\n"
                "- Social engineering signals: {se_signals}\n"
                "- Confidence: {confidence_label} ({confidence_score}/100)\n\n"
                'Content:\n"""\n{text}\n"""\n\n'
                "Return JSON:\n"
                '{{\n'
                '  "ai_explanation": "One cohesive paragraph (4-6 sentences) covering: '
                "manipulation tactics, psychological mechanisms, audience vulnerability, "
                'and contextual trust impact based on detected signals.",\n'
                '  "recommendation": "One or two sentences on verification guidance."\n'
                '}}'
            ),
        )

    @staticmethod
    def _social_engineering_v1() -> PromptTemplate:
        return PromptTemplate(
            name="social_engineering",
            version="v1",
            description="Targeted social engineering analysis",
            system_instruction=(
                "You are Technoax social engineering analysis engine. "
                "You identify and explain social engineering manipulation tactics. "
                "RULES: "
                "1) Return ONLY valid JSON. "
                "2) Focus on authority abuse, reciprocity exploitation, scarcity tactics, "
                "and social proof manipulation. "
                "3) Rate severity of each detected tactic."
            ),
            user_template=(
                "Analyze the following content for social engineering tactics.\n\n"
                "Already detected by rule-based engine:\n"
                "- Categories: {se_categories}\n"
                "- Matched phrases: {se_phrases}\n\n"
                "Return JSON:\n"
                '{{\n'
                '  "social_engineering_assessment": "string — brief assessment of social engineering risk",\n'
                '  "primary_tactic": "string — the dominant social engineering tactic used",\n'
                '  "severity": "string — Low/Medium/High/Critical"\n'
                '}}\n\n'
                'Content:\n"""\n{text}\n"""'
            ),
        )

    @staticmethod
    def _contextual_risk_v1() -> PromptTemplate:
        return PromptTemplate(
            name="contextual_risk",
            version="v1",
            description="Contextual risk analysis with domain-weighted assessment",
            system_instruction=(
                "You are Technoax risk intelligence engine. "
                "You assess the real-world danger of manipulative content "
                "considering its domain context and potential impact. "
                "RULES: "
                "1) Return ONLY valid JSON. "
                "2) Medical misinformation is more dangerous than entertainment clickbait. "
                "3) Financial manipulation with false claims is high-risk. "
                "4) Consider audience vulnerability."
            ),
            user_template=(
                "Assess the real-world risk of this content.\n\n"
                "Analysis context:\n"
                "- Domain: {domain}\n"
                "- Trust score: {trust_score}/100\n"
                "- Detected patterns: {patterns}\n"
                "- Social engineering: {se_signals}\n\n"
                "Return JSON:\n"
                '{{\n'
                '  "risk_assessment": "string — professional risk assessment",\n'
                '  "threat_level": "string — Low/Medium/High/Critical",\n'
                '  "potential_harm": "string — what could happen if audience acts on this content"\n'
                '}}\n\n'
                'Content:\n"""\n{text}\n"""'
            ),
        )


def get_prompt_registry() -> PromptRegistry:
    """Return the singleton prompt registry."""
    return PromptRegistry()
