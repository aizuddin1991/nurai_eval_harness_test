# evaluator/embeddings.py
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

# Load a lightweight, open-source embedding model once
# You can swap this out for another model if needed
_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def embed_texts(texts: List[str]) -> np.ndarray:
    """
    Generate embeddings for a list of texts.
    Returns a 2D numpy array (n_texts x dim).
    """
    return np.array(_model.encode(texts, convert_to_numpy=True, normalize_embeddings=True))

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.
    """
    return float(np.dot(vec1, vec2))

def semantic_similarity(text1: str, text2: str) -> float:
    """
    Convenience wrapper: embed two texts and return cosine similarity.
    """
    embeddings = embed_texts([text1, text2])
    return cosine_similarity(embeddings[0], embeddings[1])

def is_correct(model_answer: str, gt_answer: str, threshold: float = 0.78) -> bool:
    """
    Compare model answer to ground truth using semantic similarity.
    Returns True if similarity >= threshold.
    """
    score = semantic_similarity(model_answer, gt_answer)
    return score >= threshold, score
