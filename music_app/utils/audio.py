import librosa
import numpy as np
from typing import Dict, Any

def analyze_file(file_path: str) -> Dict[str, Any]:
    """Run librosa analysis on audio and return features dict."""
    try:
        y, sr = librosa.load(file_path, sr=None, mono=True)
    except Exception as e:
        raise ValueError(f"Could not load audio file: {e}")

    duration = float(librosa.get_duration(y=y, sr=sr))
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = [float(t) for t in librosa.frames_to_time(beat_frames, sr=sr)]

    # Key detection
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    chroma_mean = chroma.mean(axis=1)
    key_index = int(np.argmax(chroma_mean))
    key_labels = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
    detected_key = key_labels[key_index]

    # Features
    spectral_centroid = float(librosa.feature.spectral_centroid(y=y, sr=sr).mean())
    spectral_contrast = float(librosa.feature.spectral_contrast(y=y, sr=sr).mean())
    zcr = float(librosa.feature.zero_crossing_rate(y).mean())
    mfcc = [float(x) for x in librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).mean(axis=1)]
    rms = float(librosa.feature.rms(y=y).mean())

    # Derived features (scaled to 0–1 where possible)
    energy = float(min(1.0, rms / 0.1))
    danceability = float(min(1.0, tempo / 200.0))
    valence = float(np.clip(0.5 + (spectral_centroid/5000.0) - (spectral_contrast/5000.0), 0, 1))
    acousticness = float(max(0.0, 1.0 - (spectral_centroid / 5000.0)))
    instrumentalness = float(max(0.0, 1.0 - zcr))
    liveness = float(np.random.rand())

    return {
        "duration": duration,
        "tempo_bpm": float(tempo),
        "beat_times": beat_times[:20],  # cap at 20 for consistency
        "key": detected_key,
        "spectral_centroid": spectral_centroid,
        "spectral_contrast": spectral_contrast,
        "zero_crossing_rate": zcr,
        "mfcc": mfcc,
        "rms_energy": rms,
        "energy": energy,
        "danceability": danceability,
        "valence": valence,
        "acousticness": acousticness,
        "instrumentalness": instrumentalness,
        "liveness": liveness,
    }

def features_to_vector(features: Dict[str, Any]) -> np.ndarray:
    """
    Convert features dict into a numeric vector for similarity comparisons.
    Non-numeric values (e.g., key, beat_times) are excluded.
    """
    vector_parts = [
        features.get("duration", 0.0),
        features.get("tempo_bpm", 0.0),
        features.get("spectral_centroid", 0.0),
        features.get("spectral_contrast", 0.0),
        features.get("zero_crossing_rate", 0.0),
        features.get("rms_energy", 0.0),
        features.get("energy", 0.0),
        features.get("danceability", 0.0),
        features.get("valence", 0.0),
        features.get("acousticness", 0.0),
        features.get("instrumentalness", 0.0),
        features.get("liveness", 0.0),
    ] + features.get("mfcc", [])

    return np.array(vector_parts, dtype=float)
