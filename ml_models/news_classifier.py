"""
Model 2: NLP News Urgency Classifier
======================================
Uses HuggingFace zero-shot classification (DistilBERT) to assess
the urgency of disaster news headlines.

Returns a score 0–100. Falls back to keyword matching if model unavailable.
"""

import logging
logger = logging.getLogger(__name__)

_pipeline = None
_pipeline_loaded = False

def _load_pipeline():
    """Lazy-load the HuggingFace pipeline (downloads ~250MB on first run)."""
    global _pipeline, _pipeline_loaded
    if _pipeline_loaded:
        return _pipeline
    try:
        from transformers import pipeline
        _pipeline = pipeline(
            "zero-shot-classification",
            model="typeform/distilbert-base-uncased-mnli",
            multi_label=False
        )
        logger.info("[NLP Classifier] DistilBERT zero-shot pipeline loaded.")
    except Exception as e:
        logger.warning(f"[NLP Classifier] Failed to load transformers pipeline: {e}. Falling back to keyword scoring.")
        _pipeline = None
    _pipeline_loaded = True
    return _pipeline


CANDIDATE_LABELS = ["urgent life-threatening disaster", "moderate disaster concern", "routine news"]

# Keyword fallback (original logic)
KEYWORDS = {
    "trapped": 15, "collapse": 15, "buried": 15,
    "casualty": 10, "dead": 10, "killed": 10,
    "emergency": 5, "rescue": 5, "help": 5,
    "critical": 5, "damage": 5, "destroyed": 10,
    "missing": 5, "evacuate": 5, "tsunami": 20
}

def _keyword_score(articles: list) -> int:
    score = 0
    for art in articles[:10]:
        title = art.get("title", "").lower()
        for word, pts in KEYWORDS.items():
            if word in title:
                score += pts
    return min(100, score)


def calculate_news_urgency_nlp(articles: list) -> int:
    """
    Analyze news headlines for urgency using NLP zero-shot classification.
    Returns a score 0–100.
    """
    if not articles:
        return 0

    pipe = _load_pipeline()

    if pipe is None:
        # Fallback to keyword scoring
        return _keyword_score(articles)

    try:
        # Build combined text from top 5 headlines
        headlines = [a.get("title", "") for a in articles[:5] if a.get("title")]
        if not headlines:
            return 0

        combined = " | ".join(headlines)

        result = pipe(combined, candidate_labels=CANDIDATE_LABELS)

        # Map label scores to 0-100
        score_map = {}
        for label, score in zip(result["labels"], result["scores"]):
            score_map[label] = score

        urgent_conf = score_map.get("urgent life-threatening disaster", 0)
        moderate_conf = score_map.get("moderate disaster concern", 0)

        # Weighted: urgent → up to 100, moderate → up to 50
        nlp_score = int((urgent_conf * 100) + (moderate_conf * 50))
        nlp_score = min(100, nlp_score)

        logger.info(f"[NLP Classifier] Urgency score: {nlp_score} (urgent={urgent_conf:.2f}, moderate={moderate_conf:.2f})")
        return nlp_score

    except Exception as e:
        logger.warning(f"[NLP Classifier] Inference failed: {e}. Falling back to keyword scoring.")
        return _keyword_score(articles)
