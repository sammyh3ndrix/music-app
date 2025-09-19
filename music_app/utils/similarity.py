import numpy as np
from typing import Dict, List, Tuple, Optional

FEATURE_KEYS = [
    "tempo_bpm", "spectral_centroid", "spectral_contrast", "zero_crossing_rate",
    "rms_energy", "energy", "danceability", "valence", "acousticness",
    "instrumentalness", "liveness"
]
MFCC_DIM = 13


def features_to_vector(feat: Dict) -> Optional[np.ndarray]:
    """Convert feature dict into a numeric vector suitable for similarity."""
    if not feat or not isinstance(feat, dict):
        return None

    vec = []
    # Core scalar features
    for k in FEATURE_KEYS:
        vec.append(float(feat.get(k, 0.0)))

    # MFCCs (pad/truncate to MFCC_DIM)
    mfcc = feat.get("mfcc") or []
    mfcc = [float(x) for x in mfcc[:MFCC_DIM]]
    if len(mfcc) < MFCC_DIM:
        mfcc += [0.0] * (MFCC_DIM - len(mfcc))

    vec.extend(mfcc)
    return np.array(vec, dtype=float)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    if a is None or b is None:
        return 0.0
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def top_k_similar(
    target_features: Dict,
    candidates: List[Tuple[int, Dict]],
    k: int = 5
) -> List[Tuple[int, float]]:
    """
    Compute top-k most similar uploads.
    
    Args:
        target_features: feature dict of the target upload.
        candidates: list of (upload_id, feature_dict).
        k: number of results to return.
    
    Returns:
        List of (upload_id, similarity_score) sorted descending.
    """
    target_vec = features_to_vector(target_features)
    results = []
    for upload_id, feat in candidates:
        vec = features_to_vector(feat)
        score = cosine_similarity(target_vec, vec)
        results.append((upload_id, score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:k]
