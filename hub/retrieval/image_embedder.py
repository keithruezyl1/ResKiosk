"""
hub/retrieval/image_embedder.py

Phase 9 / Slice 7C — local CLIP image/text encoder (D16).

CLIP ViT-B/32 via sentence-transformers: encodes images AND text into one shared
space, so an English text query can be matched against image vectors. Loaded
offline from a bundled dir (mirrors hub/retrieval/embedder.py), CPU, Apache-2.0.

The encoder is loaded lazily and is a process singleton. Tests patch the
module-level `SentenceTransformer` (and point RESKIOSK_CLIP_MODEL_PATH at a temp
dir) so the real ~hundreds-of-MB model is never loaded in unit tests.
"""

import os
import logging
from pathlib import Path
from typing import Union

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Model identity — persisted with each embedding so a model change invalidates them.
MODEL_NAME = "clip-ViT-B-32"
MODEL_VERSION = "clip-ViT-B-32@st"
EMBED_DIM = 512

_instance = None


def get_clip_model_path() -> str:
    path = os.environ.get("RESKIOSK_CLIP_MODEL_PATH")
    if path:
        return path
    reskiosk_root = Path(__file__).resolve().parent.parent.parent
    return str(reskiosk_root / "packaging" / "hub_models" / "clip")


class ImageEmbedder:
    def __init__(self):
        model_path = get_clip_model_path()
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"CLIP model path does not exist: {model_path}\n"
                "Run packaging/bundle_models.py (bundle_clip) to download the model."
            )
        logger.info(f"[ImageEmbedder] loading {MODEL_NAME} from {model_path}")
        self.model = SentenceTransformer(model_path, device="cpu", local_files_only=True)
        self.model_name = MODEL_NAME
        self.model_version = MODEL_VERSION

    def embed_text(self, text: Union[str, list]) -> np.ndarray:
        """Encode an English query into the shared CLIP space."""
        return self.model.encode(text, convert_to_numpy=True)

    def embed_image(self, image) -> np.ndarray:
        """Encode an image (PIL.Image, or a path/str) into the shared CLIP space."""
        if isinstance(image, (str, Path)):
            from PIL import Image as PILImage
            image = PILImage.open(image).convert("RGB")
        return self.model.encode(image, convert_to_numpy=True)


def load_image_embedder() -> ImageEmbedder:
    global _instance
    if _instance is None:
        _instance = ImageEmbedder()
    return _instance


def reset_image_embedder() -> None:
    """Test/maintenance hook — drop the cached singleton."""
    global _instance
    _instance = None


def needs_embedding(asset, model_version: str = MODEL_VERSION) -> bool:
    """True if a ready asset has no current-model embedding yet."""
    return asset.embedding is None or asset.embedding_model != model_version


def generate_and_store_embedding(db, asset, kb_version=None, embedder=None) -> bool:
    """S7C.3/4: encode a `ready` asset's image and persist the vector + model +
    KB version. Readiness-gated: non-`ready` assets are skipped (return False).
    Failures are logged and leave the asset embedding-less (→ excluded from
    retrieval) rather than raising. Returns True if an embedding was written."""
    from hub.services import image_assets as ia
    from hub.retrieval.embedder import serialize_embedding

    if asset.status != ia.STATUS_READY:
        logger.info(f"[ImageEmbedder] skip asset_id={asset.id} status={asset.status} (not ready)")
        return False
    path = ia.variant_path(asset, ia.VARIANT_ORIGINAL)
    if path is None or not path.exists():
        logger.warning(f"[ImageEmbedder] asset_id={asset.id} original missing; cannot embed")
        return False
    try:
        emb = embedder or load_image_embedder()
        vec = emb.embed_image(path)
        asset.embedding = serialize_embedding(np.asarray(vec, dtype=np.float32))
        asset.embedding_model = emb.model_version
        asset.embedding_kb_version = kb_version
        db.commit()
        logger.info(f"[ImageEmbedder] embedded asset_id={asset.id} model={emb.model_version} kb_version={kb_version}")
        return True
    except Exception:
        logger.exception(f"[ImageEmbedder] embedding failed for asset_id={asset.id}")
        db.rollback()
        return False


def embed_ready_assets(db, kb_version, embedder=None) -> int:
    """Publish-time batch: ensure every `ready` asset referenced by an enabled
    image KB item has a current-model embedding (stamped with kb_version). Loads
    the encoder only if there's work to do. Returns the count newly embedded."""
    from hub.db import schema
    from hub.services import image_assets as ia

    rows = (
        db.query(schema.KBItem.image_asset_id)
        .filter(schema.KBItem.enabled == 1, schema.KBItem.image_asset_id.isnot(None))
        .all()
    )
    ids = {r[0] for r in rows if r[0] is not None}
    if not ids:
        return 0
    assets = (
        db.query(schema.ImageAsset)
        .filter(schema.ImageAsset.id.in_(ids), schema.ImageAsset.status == ia.STATUS_READY)
        .all()
    )
    todo = [a for a in assets if needs_embedding(a)]
    # Re-stamp KB version on already-embedded assets without recomputing the vector.
    for a in assets:
        if not needs_embedding(a):
            a.embedding_kb_version = kb_version
    db.commit()
    if not todo:
        return 0
    emb = embedder or load_image_embedder()  # load once, only when work exists
    n = 0
    for a in todo:
        if generate_and_store_embedding(db, a, kb_version, embedder=emb):
            n += 1
    return n


def cosine_sim(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Row-wise cosine similarity of a query vector against a matrix of vectors.
    Deterministic; guards zero-norm rows."""
    q = np.asarray(query_vec, dtype=np.float64).reshape(-1)
    m = np.asarray(matrix, dtype=np.float64)
    if m.ndim == 1:
        m = m.reshape(1, -1)
    qn = np.linalg.norm(q) or 1.0
    mn = np.linalg.norm(m, axis=1)
    mn[mn == 0] = 1.0
    return (m @ q) / (mn * qn)
