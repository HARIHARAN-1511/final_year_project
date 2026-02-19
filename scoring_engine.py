
import os
import math
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model 1: ML Severity Classifier
# ---------------------------------------------------------------------------
_severity_model = None
_severity_model_loaded = False

def _load_severity_model():
    global _severity_model, _severity_model_loaded
    if _severity_model_loaded:
        return _severity_model
    try:
        import joblib
        model_path = os.path.join(os.path.dirname(__file__), "ml_models", "severity_model.pkl")
        if os.path.exists(model_path):
            _severity_model = joblib.load(model_path)
            logger.info("[SeverityClassifier] sklearn RandomForest model loaded.")
        else:
            logger.warning("[SeverityClassifier] severity_model.pkl not found. Run ml_models/train_severity_classifier.py first. Using rule-based fallback.")
    except Exception as e:
        logger.warning(f"[SeverityClassifier] Failed to load model: {e}. Using fallback.")
        _severity_model = None
    _severity_model_loaded = True
    return _severity_model


def predict_severity(magnitude: float, depth_km: float = 30.0, tsunami_flag: int = 0) -> str:
    """
    Predict disaster severity using the trained RandomForest classifier.
    Falls back to rule-based thresholds if model is unavailable.
    
    Returns: "CATASTROPHIC" | "SEVERE" | "MODERATE" | "MINOR"
    """
    import numpy as np
    model = _load_severity_model()
    
    if model is not None:
        try:
            X = np.array([[magnitude, depth_km, int(tsunami_flag)]])
            pred = model.predict(X)[0]
            logger.debug(f"[SeverityClassifier] mag={magnitude}, depth={depth_km}, tsunami={tsunami_flag} → {pred}")
            return pred
        except Exception as e:
            logger.warning(f"[SeverityClassifier] Prediction failed: {e}. Using rule-based fallback.")
    
    # Rule-based fallback (original logic)
    if magnitude >= 7.0:
        return "CATASTROPHIC"
    elif magnitude >= 6.0:
        return "SEVERE"
    elif magnitude >= 4.5:
        return "MODERATE"
    else:
        return "MINOR"


# ---------------------------------------------------------------------------
# Model 1b: ML Cyclone Severity Classifier
# ---------------------------------------------------------------------------
_cyclone_model = None
_cyclone_model_loaded = False

def _load_cyclone_model():
    global _cyclone_model, _cyclone_model_loaded
    if _cyclone_model_loaded:
        return _cyclone_model
    try:
        import joblib
        model_path = os.path.join(os.path.dirname(__file__), "ml_models", "cyclone_severity_model.pkl")
        if os.path.exists(model_path):
            _cyclone_model = joblib.load(model_path)
            logger.info("[CycloneClassifier] sklearn RandomForest model loaded.")
        else:
            logger.warning("[CycloneClassifier] cyclone_severity_model.pkl not found. Run ml_models/train_cyclone_severity_classifier.py first. Using rule-based fallback.")
    except Exception as e:
        logger.warning(f"[CycloneClassifier] Failed to load model: {e}. Using fallback.")
        _cyclone_model = None
    _cyclone_model_loaded = True
    return _cyclone_model


def predict_cyclone_severity(intensity_kt: int, pressure_hpa: float = None, intensification_rate: float = 0.0) -> str:
    """
    Predict cyclone severity using the trained RandomForest classifier.
    Features: [wind_speed_kt, pressure_hpa, intensification_rate_kt_per_6h]
    Falls back to Saffir-Simpson thresholds if model is unavailable.
    
    Returns: "CATASTROPHIC" | "SEVERE" | "MODERATE" | "MINOR" | "NONE"
    """
    import numpy as np
    model = _load_cyclone_model()
    
    # Estimate pressure from wind speed if not provided (empirical)
    if pressure_hpa is None or pressure_hpa <= 0:
        pressure_hpa = max(880, min(1013, 1010 - intensity_kt * 1.0))
    
    if model is not None:
        try:
            X = np.array([[float(intensity_kt), float(pressure_hpa), float(intensification_rate)]])
            pred = model.predict(X)[0]
            logger.debug(f"[CycloneClassifier] wind={intensity_kt}kt, p={pressure_hpa}hPa, intens={intensification_rate} → {pred}")
            return pred
        except Exception as e:
            logger.warning(f"[CycloneClassifier] Prediction failed: {e}. Using rule-based fallback.")
    
    # Rule-based fallback (Saffir-Simpson / JTWC thresholds)
    if intensity_kt >= 115:
        return "CATASTROPHIC"
    elif intensity_kt >= 65:
        return "SEVERE"
    elif intensity_kt >= 34:
        return "MODERATE"
    elif intensity_kt > 0:
        return "MINOR"
    return "NONE"


# ---------------------------------------------------------------------------
# Priority Scoring (unchanged)
# ---------------------------------------------------------------------------

def calculate_priority_score(
    severity: str,
    population_exposure: int,
    resource_distance_km: float,
    news_urgency_score: int
) -> float:
    """
    Calculate a 0-100 priority score based on a weighted formula:
    Score = (0.4 * Scaled_Severity) + (0.3 * Scaled_Pop) + (0.2 * Scaled_Dist) + (0.1 * News)
    """
    
    # 1. Severity Score (0-100)
    severity_map = {
        "CATASTROPHIC": 100,
        "SEVERE": 80,
        "MODERATE": 50,
        "MINOR": 20,
        "NONE": 0,
        "UNKNOWN": 10
    }
    s_score = severity_map.get(severity, 10)

    # 2. Population Score (0-100) — log scale
    if population_exposure <= 0:
        p_score = 0
    else:
        p_score = min(100, math.log10(population_exposure + 1) * 16.6)

    # 3. Resource Distance Score (0-100)
    if resource_distance_km < 0:
        d_score = 50
    else:
        d_score = min(100, resource_distance_km)

    # 4. News Urgency (0-100)
    n_score = min(100, max(0, news_urgency_score))

    # Weighted Sum: Severity 40%, Pop 30%, Distance 20%, News 10%
    final_score = (0.4 * s_score) + (0.3 * p_score) + (0.2 * d_score) + (0.1 * n_score)
    
    return round(final_score, 1)


def get_priority_label(score: float) -> str:
    if score >= 85:
        return "CRITICAL"
    elif score >= 60:
        return "HIGH"
    elif score >= 30:
        return "MEDIUM"
    else:
        return "LOW"


# ---------------------------------------------------------------------------
# Model 2: NLP News Urgency Classifier (delegates to ml_models/news_classifier.py)
# ---------------------------------------------------------------------------

def calculate_news_urgency(articles: list) -> int:
    """
    Analyze news headlines for urgency using NLP (DistilBERT zero-shot).
    Falls back to keyword scoring if transformer model is unavailable.
    Returns a score 0-100.
    """
    try:
        from ml_models.news_classifier import calculate_news_urgency_nlp
        return calculate_news_urgency_nlp(articles)
    except Exception as e:
        logger.warning(f"[NLP Classifier] Module import failed: {e}. Using keyword fallback.")
        return _keyword_fallback(articles)


def _keyword_fallback(articles: list) -> int:
    """Original keyword-matching urgency scorer as a safety net."""
    if not articles:
        return 0
    keywords = {
        "trapped": 15, "collapse": 15, "buried": 15,
        "casualty": 10, "dead": 10, "killed": 10,
        "emergency": 5, "rescue": 5, "help": 5,
        "critical": 5, "damage": 5, "destroyed": 10,
        "missing": 5, "evacuate": 5, "tsunami": 20
    }
    score = 0
    for art in articles[:10]:
        title = art.get("title", "").lower()
        for word, points in keywords.items():
            if word in title:
                score += points
    return min(100, score)
