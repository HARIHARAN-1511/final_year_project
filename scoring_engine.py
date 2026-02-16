
import math

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

    # 2. Population Score (0-100)
    # Log scale: 10 people -> ~10, 100 people -> ~20, 1M people -> 100
    # Formula: min(100, log10(pop + 1) * 16.6)
    if population_exposure <= 0:
        p_score = 0
    else:
        p_score = min(100, math.log10(population_exposure + 1) * 16.6)

    # 3. Resource Distance Score (0-100)
    # Closer resources = GOOD (Lower Urgency for *access*? No, wait.)
    # Actually, if resources are FAR, the situation is MORE CRITICAL?
    # Or is "Priority" about "Where should we send help?"
    # High Priority = Needs Help Now.
    # If resources are far, it's harder to help, but maybe needed more?
    # Let's assume: Far resources = Higher Vulnerability = Higher Priority score.
    # 0km -> 0 score (Safe), 100km+ -> 100 score (Critical isolation)
    if resource_distance_km < 0: # Unknown
        d_score = 50
    else:
        d_score = min(100, resource_distance_km) 

    # 4. News Urgency (0-100)
    # Provided directly by the news analyzer (0-5 scale mapped to 0-100?)
    # Let's assume input is 0-100 or map it.
    # If input is raw article count or keywords, we need to map it.
    # Let's assume the caller passes a normalized 0-100 score.
    n_score = min(100, max(0, news_urgency_score))

    # Weighted Sum
    # Weights: Severity 40%, Pop 30%, Distance 20%, News 10%
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

def calculate_news_urgency(articles: list) -> int:
    """
    Analyze news headlines for urgency keywords.
    Returns a score 0-100.
    """
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
    # Analyze max 10 articles to check for keyword density
    for art in articles[:10]:
        title = art.get("title", "").lower()
        for word, points in keywords.items():
            if word in title:
                score += points
                
    # Normalize: >100 is max (e.g., 5 articles saying "trapped" = 75 points)
    return min(100, score)

