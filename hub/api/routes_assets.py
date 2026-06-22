"""
hub/api/routes_assets.py

Phase 8 / Slice 7B — image asset API.
  - POST /admin/kb/assets          upload an image (admin); store + derive; optional KB-item link
  - GET  /admin/kb/assets          list assets + status (admin confirmation view backend)
  - GET  /admin/kb/assets/{id}     single asset status/metadata (admin)
  - GET  /assets/{id}/{variant}    serve a variant to the kiosk — ONLY if `ready` (4-state gate)
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from hub.db.session import get_db
from hub.db import schema
from hub.services import image_assets as ia
from hub.api.routes_auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

# Reason codes that are the caller's fault (reject) vs a processing failure.
_REJECT_REASONS = {ia.REASON_UNSUPPORTED_MIME, ia.REASON_TOO_LARGE}

_VARIANT_MEDIA = {ia.VARIANT_THUMB: "image/webp", ia.VARIANT_DISPLAY: "image/webp"}


def _asset_dict(a: schema.ImageAsset) -> dict:
    return {
        "id": a.id,
        "status": a.status,
        "content_hash": a.content_hash,
        "mime": a.mime,
        "size_bytes": a.size_bytes,
        "width": a.width,
        "height": a.height,
        "kb_version": a.kb_version,
        "failure_reason": a.failure_reason,
        "render_ref": ia.render_ref(a.id) if a.status == ia.STATUS_READY else None,
        "thumb_ref": ia.render_ref(a.id, ia.VARIANT_THUMB) if a.status == ia.STATUS_READY else None,
    }


@router.post("/admin/kb/assets")
async def upload_asset(
    file: UploadFile = File(...),
    kb_item_id: int | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: schema.User | None = Depends(get_current_user),
):
    data = await file.read()
    try:
        asset = ia.store_asset(db, data, file.content_type)
    except ia.AssetError as e:
        # Persist a failed/rejected row for audit + admin visibility (S7B.5/9).
        status = ia.STATUS_REJECTED if e.reason in _REJECT_REASONS else ia.STATUS_FAILED
        try:
            row = schema.ImageAsset(
                content_hash=ia.sha256_hex(data),
                mime=file.content_type,
                size_bytes=len(data),
                status=status,
                failure_reason=e.reason,
            )
            db.add(row)
            db.commit()
        except Exception:
            db.rollback()
        logger.warning(f"[Assets] upload rejected/failed reason={e.reason} status={status}")
        raise HTTPException(status_code=422 if status == ia.STATUS_FAILED else 400,
                            detail={"reason": e.reason, "status": status})

    # Optional: link the asset to a KB image item.
    if kb_item_id is not None:
        item = db.query(schema.KBItem).filter(schema.KBItem.id == kb_item_id).first()
        if item:
            item.image_asset_id = asset.id
            item.modality = "image"
            db.commit()

    logger.info(f"[Assets] uploaded asset_id={asset.id} by={getattr(current_user, 'username', None)}")
    return _asset_dict(asset)


@router.get("/admin/kb/assets")
async def list_assets(db: Session = Depends(get_db), current_user: schema.User | None = Depends(get_current_user)):
    rows = db.query(schema.ImageAsset).order_by(schema.ImageAsset.id.desc()).all()
    return [_asset_dict(a) for a in rows]


@router.get("/admin/kb/assets/{asset_id}")
async def get_asset_status(asset_id: int, db: Session = Depends(get_db),
                           current_user: schema.User | None = Depends(get_current_user)):
    asset = db.query(schema.ImageAsset).filter(schema.ImageAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="asset not found")
    return _asset_dict(asset)


@router.get("/assets/search")
async def search_images(q: str, db: Session = Depends(get_db)):
    """Kiosk-facing text->image semantic search (Phase 9). Returns ranked image
    evidence above the similarity floor (modality, score, rank, render_ref)."""
    from hub.retrieval import search
    results = search.retrieve_images(db, q)
    return {"query": q, "results": results}


@router.get("/assets/{asset_id}/{variant}")
async def serve_asset(asset_id: int, variant: str, db: Session = Depends(get_db)):
    """Kiosk-facing. Serves a variant ONLY for `ready` assets (4-state gate);
    pending/failed/rejected are indistinguishable from missing → 404."""
    asset = db.query(schema.ImageAsset).filter(schema.ImageAsset.id == asset_id).first()
    if not ia.is_resident_facing(asset):
        raise HTTPException(status_code=404, detail="asset not available")
    path = ia.variant_path(asset, variant)
    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail="variant not found")
    media_type = _VARIANT_MEDIA.get(variant, asset.mime or "application/octet-stream")
    return FileResponse(str(path), media_type=media_type)
