"""
Model 5b: Cyclone Anomaly Detector
=====================================
Uses IsolationForest to detect statistically unusual cyclone events
in the live feed based on: wind speed (intensity_kt) and derived features.

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
            contamination=0.15,  # cyclone feeds are small; slightly higher threshold
            random_state=42
        )
        logger.info("[CycloneAnomalyDetector] IsolationForest initialized.")
    except Exception as e:
        logger.warning(f"[CycloneAnomalyDetector] Init failed: {e}")
        _detector = None
    _detector_fitted = True
    return _detector


def _parse_intensity(val) -> float:
    """Safely parse intensity value which may be a string like '125'."""
    try:
        return float(str(val).strip())
    except (ValueError, TypeError):
        return 0.0


def flag_anomalous_cyclones(events: list) -> list:
    """
    Given a list of cyclone event dicts, fits IsolationForest on
    [intensity_kt, estimated_pressure] and flags anomalies.

    Returns the same list with `is_anomaly` and `anomaly_note` keys added.
    """
    if not events:
        return events

    detector = _get_detector()
    if detector is None:
        for e in events:
            e["is_anomaly"] = False
            e["anomaly_note"] = ""
        return events

    try:
        features = []
        for ev in events:
            wind_kt = _parse_intensity(ev.get("intensity", 0))
            # Estimate pressure from wind if not available
            pressure = float(ev.get("pressure") or max(880, 1010 - wind_kt))
            features.append([wind_kt, pressure])

        X = np.array(features)

        if len(X) < 3:
            # Too few storms to meaningfully apply IsolationForest
            for e in events:
                e["is_anomaly"] = False
                e["anomaly_note"] = ""
            return events

        detector.fit(X)
        preds = detector.predict(X)

        for ev, pred, (wind_kt, pressure) in zip(events, preds, features):
            if pred == -1:
                ev["is_anomaly"] = True
                reasons = []
                if wind_kt >= 130:
                    reasons.append(f"extreme wind speed ({int(wind_kt)} kt)")
                if pressure < 920:
                    reasons.append(f"extremely low pressure ({int(pressure)} hPa)")
                if wind_kt >= 115 and pressure < 930:
                    reasons.append("rapid intensification pattern")
                note = "Unusual cyclone detected" + (": " + ", ".join(reasons) if reasons else " — statistical outlier")
                ev["anomaly_note"] = note
            else:
                ev["is_anomaly"] = False
                ev["anomaly_note"] = ""

        anomaly_count = sum(1 for p in preds if p == -1)
        logger.info(f"[CycloneAnomalyDetector] Flagged {anomaly_count}/{len(events)} cyclones as anomalous.")

    except Exception as e:
        logger.warning(f"[CycloneAnomalyDetector] Inference failed: {e}")
        for ev in events:
            ev["is_anomaly"] = False
            ev["anomaly_note"] = ""

    return events
