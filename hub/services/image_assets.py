"""
hub/services/image_assets.py

Phase 8 / Slice 7B — image asset lifecycle (Goal 2, D14/D15).

Binaries are stored on the **filesystem** under the assets dir (next to the DB,
override RESKIOSK_ASSETS_DIR), **content-addressed** by sha256 with sharded
directories. Each asset gets a deterministic **thumbnail** + one compressed
**display rendition** (Pillow, fixed params → reproducible bytes). Identity +
lifecycle metadata live in the `image_assets` table; only `ready` assets are
resident-facing (4-state model). Global dedup by content hash.

No cloud, no AI upscaling. Admin-only uploads; decompression-bomb guarded.
"""

from __future__ import annotations

import hashlib
import io
import logging
import os
from pathlib import Path
from typing import Optional

from PIL import Image, ImageOps

from hub.db import schema
from hub.db.session import get_db_url

logger = logging.getLogger(__name__)

# ── states (D15) ─────────────────────────────────────────────────────────────
STATUS_PENDING = "pending"
STATUS_READY = "ready"
STATUS_FAILED = "failed"
STATUS_REJECTED = "rejected"
RESIDENT_FACING_STATUS = STATUS_READY

# Stable failure/rejection reason codes.
REASON_UNSUPPORTED_MIME = "unsupported_mime"
REASON_TOO_LARGE = "too_large"
REASON_DECODE_FAILED = "decode_failed"
REASON_TOO_MANY_PIXELS = "too_many_pixels"

# ── policy / deterministic params ────────────────────────────────────────────
ALLOWED_MIME = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}
MAX_BYTES = int(os.environ.get("RESKIOSK_ASSET_MAX_BYTES", 8 * 1024 * 1024))  # 8 MB
THUMB_MAX = 256          # longest edge, px
RENDITION_MAX = 1024     # longest edge, px
WEBP_QUALITY = 80
WEBP_METHOD = 6          # deterministic encoder effort
# Decompression-bomb guard (Pillow default ~89M; tighten for a kiosk).
Image.MAX_IMAGE_PIXELS = int(os.environ.get("RESKIOSK_ASSET_MAX_PIXELS", 40_000_000))

VARIANT_THUMB = "thumb"
VARIANT_DISPLAY = "display"
VARIANT_ORIGINAL = "original"


class AssetError(Exception):
    """Raised for a rejected/failed asset; carries a stable reason code."""
    def __init__(self, reason: str, message: str = ""):
        super().__init__(message or reason)
        self.reason = reason


def assets_dir() -> Path:
    """Writable assets directory: RESKIOSK_ASSETS_DIR, else <db_dir>/assets."""
    override = os.environ.get("RESKIOSK_ASSETS_DIR")
    if override:
        base = Path(override)
    else:
        # Derive from the DB url (sqlite:///<path>); assets live beside the DB.
        url = get_db_url()
        db_path = url.replace("sqlite:///", "", 1)
        base = Path(db_path).parent / "assets"
    base.mkdir(parents=True, exist_ok=True)
    return base


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sharded_relpath(content_hash: str, suffix: str, ext: str) -> str:
    """Relative content-addressed path: <hash[:2]>/<hash><suffix>.<ext>."""
    name = f"{content_hash}{suffix}.{ext}"
    return str(Path(content_hash[:2]) / name)


def _abs(relpath: str) -> Path:
    return assets_dir() / relpath


def _load_image(data: bytes) -> Image.Image:
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Image.DecompressionBombError as e:
        raise AssetError(REASON_TOO_MANY_PIXELS, str(e))
    except Exception as e:
        raise AssetError(REASON_DECODE_FAILED, str(e))
    # Normalize EXIF orientation so derived bytes are deterministic regardless of camera flags.
    img = ImageOps.exif_transpose(img)
    return img.convert("RGB")


def _encode_variant(img: Image.Image, max_edge: int) -> bytes:
    """Aspect-preserving downscale to a max edge + deterministic WEBP encode.
    No upscaling (thumbnail only shrinks); no cropping."""
    work = img.copy()
    work.thumbnail((max_edge, max_edge), Image.LANCZOS)  # preserves aspect; shrink-only
    buf = io.BytesIO()
    work.save(buf, format="WEBP", quality=WEBP_QUALITY, method=WEBP_METHOD)
    return buf.getvalue()


def generate_thumbnail(data: bytes) -> bytes:
    return _encode_variant(_load_image(data), THUMB_MAX)


def generate_rendition(data: bytes) -> bytes:
    return _encode_variant(_load_image(data), RENDITION_MAX)


def _validate(data: bytes, mime: Optional[str]) -> str:
    if mime not in ALLOWED_MIME:
        raise AssetError(REASON_UNSUPPORTED_MIME, f"mime={mime}")
    if len(data) > MAX_BYTES:
        raise AssetError(REASON_TOO_LARGE, f"{len(data)} > {MAX_BYTES}")
    return ALLOWED_MIME[mime]


def store_asset(db, data: bytes, mime: Optional[str], kb_version: Optional[int] = None) -> schema.ImageAsset:
    """Validate, write original + thumbnail + rendition (content-addressed), and
    create a `ready` ImageAsset row. Global dedup: identical bytes reuse the
    existing asset. On validation/decode failure raises AssetError (callers log +
    may persist a `failed`/`rejected` row)."""
    ext = _validate(data, mime)
    content_hash = sha256_hex(data)

    existing = (
        db.query(schema.ImageAsset)
        .filter(schema.ImageAsset.content_hash == content_hash)
        .first()
    )
    if existing:
        logger.info(f"[Assets] dedup hit hash={content_hash[:12]} asset_id={existing.id}")
        return existing

    img = _load_image(data)
    width, height = img.size
    thumb_bytes = _encode_variant(img, THUMB_MAX)
    rendition_bytes = _encode_variant(img, RENDITION_MAX)

    original_ref = _sharded_relpath(content_hash, "", ext)
    thumb_ref = _sharded_relpath(content_hash, "_thumb", "webp")
    rendition_ref = _sharded_relpath(content_hash, "_disp", "webp")

    for relpath, payload in (
        (original_ref, data),
        (thumb_ref, thumb_bytes),
        (rendition_ref, rendition_bytes),
    ):
        p = _abs(relpath)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(payload)

    asset = schema.ImageAsset(
        content_hash=content_hash,
        mime=mime,
        size_bytes=len(data),
        width=width,
        height=height,
        original_ref=original_ref,
        thumb_ref=thumb_ref,
        rendition_ref=rendition_ref,
        rendition_hash=sha256_hex(rendition_bytes),
        kb_version=kb_version,
        status=STATUS_READY,
    )
    db.add(asset)
    db.commit()
    logger.info(f"[Assets] stored asset_id={asset.id} hash={content_hash[:12]} status=ready")
    return asset


def is_resident_facing(asset: Optional[schema.ImageAsset]) -> bool:
    return bool(asset) and asset.status == RESIDENT_FACING_STATUS


def variant_ref(asset: schema.ImageAsset, variant: str) -> Optional[str]:
    return {
        VARIANT_THUMB: asset.thumb_ref,
        VARIANT_DISPLAY: asset.rendition_ref,
        VARIANT_ORIGINAL: asset.original_ref,
    }.get(variant)


def variant_path(asset: schema.ImageAsset, variant: str) -> Optional[Path]:
    ref = variant_ref(asset, variant)
    return _abs(ref) if ref else None


def render_ref(asset_id: int, variant: str = VARIANT_DISPLAY) -> str:
    """The kiosk-facing URL for an asset variant (evidence contract render_ref)."""
    return f"/assets/{asset_id}/{variant}"


def set_status(db, asset: schema.ImageAsset, status: str, failure_reason: Optional[str] = None) -> schema.ImageAsset:
    """S7B.5/9: transition an asset's state and log it."""
    asset.status = status
    if failure_reason is not None:
        asset.failure_reason = failure_reason
    db.commit()
    logger.info(f"[Assets] asset_id={asset.id} -> status={status} reason={failure_reason}")
    return asset


def asset_files_ok(asset: schema.ImageAsset) -> bool:
    """S7B.9: broken/missing-artifact guard — all three variant files present."""
    for variant in (VARIANT_ORIGINAL, VARIANT_THUMB, VARIANT_DISPLAY):
        p = variant_path(asset, variant)
        if p is None or not p.exists():
            return False
    return True


def link_assets_to_kb_version(db, kb_version: int) -> int:
    """S7B.6/7: stamp the published KB version onto the `ready` assets referenced
    by enabled KB items. Content-addressed artifacts don't change across versions,
    so this is the version linkage (logs can join image evidence to a KB version)
    and the publish-time refresh point. Returns the count linked."""
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
        .filter(schema.ImageAsset.id.in_(ids), schema.ImageAsset.status == STATUS_READY)
        .all()
    )
    for a in assets:
        a.kb_version = kb_version
    db.commit()
    logger.info(f"[Assets] linked {len(assets)} ready asset(s) to kb_version={kb_version}")
    return len(assets)
