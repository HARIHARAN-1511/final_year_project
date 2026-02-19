"""
Model 5: Earthquake Anomaly Detector
=======================================
Uses IsolationForest to detect statistically unusual earthquake events
in the live feed based on: magnitude, depth_km, and significance score.

Anomalous events get flagged with is_anomaly=True and an explanatory note.
"""

import logging
import numpy as np

logger = logging.getLogger(__name__)

_detector = None
_detector_fitted = False

def _get_detector():
    """Lazy-init the IsolationForest model."""
    global _detector, _detector_fitted
    if _detector_fitted:
        return _detector
    try:
        from sklearn.ensemble import IsolationForest
        _detector = IsolationForest(
            n_estimators=100,
            contamination=0.1,  # expect ~10% anomalous events
            random_state=42
        )
        logger.info("[Anomaly Detector] IsolationForest initialized.")
    except Exception as e:
        logger.warning(f"[Anomaly Detector] Failed to init IsolationForest: {e}")
        _detector = None
    _detector_fitted = True
    return _detector


def flag_anomalous_events(events: list) -> list:
    """
    Given a list of earthquake event dicts, fits IsolationForest on
    [magnitude, depth_km, significance] and flags anomalies.

    Returns the same list with `is_anomaly` and `anomaly_note` keys added.
    """
    if not events:
        return events

    detector = _get_detector()
    if detector is None:
        # Graceful fallback — just mark everything as normal
        for e in events:
            e["is_anomaly"] = False
            e["anomaly_note"] = ""
        return events

    try:
        # Build feature matrix
        features = []
        for ev in events:
            mag = float(ev.get("magnitude") or 0)
            depth = float(ev.get("depth_km") or 0)
            sig = float(ev.get("significance") or ev.get("sig") or 0)
            features.append([mag, depth, sig])

        X = np.array(features)

        if len(X) < 5:
            # Not enough events to detect anomalies meaningfully
            for e in events:
                e["is_anomaly"] = False
                e["anomaly_note"] = ""
            return events

        # Fit on current batch (unsupervised, no training data needed)
        detector.fit(X)
        preds = detector.predict(X)       # 1 = normal, -1 = anomaly
        scores = detector.score_samples(X)  # lower = more anomalous

        for ev, pred, score in zip(events, preds, scores):
            if pred == -1:
                ev["is_anomaly"] = True
                # Generate a human-readable note explaining WHY it's unusual
                mag = float(ev.get("magnitude") or 0)
                depth = float(ev.get("depth_km") or 0)
                reasons = []
                if mag > 6.5:
                    reasons.append(f"unusually high magnitude (M{mag})")
                if depth < 5:
                    reasons.append(f"extremely shallow depth ({depth:.1f} km)")
                if depth > 500:
                    reasons.append(f"unusually deep event ({depth:.0f} km)")
                sig = float(ev.get("significance") or ev.get("sig") or 0)
                if sig > 800:
                    reasons.append(f"very high significance score ({int(sig)})")
                note = "Unusual event detected" + (": " + ", ".join(reasons) if reasons else " — statistical outlier")
                ev["anomaly_note"] = note
            else:
                ev["is_anomaly"] = False
                ev["anomaly_note"] = ""

        anomaly_count = sum(1 for p in preds if p == -1)
        logger.info(f"[Anomaly Detector] Flagged {anomaly_count}/{len(events)} events as anomalous.")

    except Exception as e:
        logger.warning(f"[Anomaly Detector] Inference failed: {e}")
        for ev in events:
            ev["is_anomaly"] = False
            ev["anomaly_note"] = ""

    return events
