"""
hub/tests/test_image_asset_api.py

Phase 8 / Slice 7B — asset API: upload (valid/invalid), admin status, and the
4-state-gated serving endpoint.
"""

import io
import os
import tempfile
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from hub.db.session import Base, get_db
from hub.db import schema
from hub.api import routes_assets
from hub.api.routes_auth import get_current_user
from hub.services import image_assets as ia


def _png(w=400, h=300) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (10, 120, 80)).save(buf, format="PNG")
    return buf.getvalue()


class TestAssetApi(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["RESKIOSK_ASSETS_DIR"] = self._tmp.name
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        self.SessionLocal = sessionmaker(bind=engine)
        self.db = self.SessionLocal()

        app = FastAPI()
        app.include_router(routes_assets.router)
        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[get_current_user] = lambda: schema.User(username="admin")
        self.client = TestClient(app)

    def tearDown(self):
        self.db.close()
        os.environ.pop("RESKIOSK_ASSETS_DIR", None)
        self._tmp.cleanup()

    def _upload(self, data=None, mime="image/png", filename="x.png"):
        data = _png() if data is None else data
        return self.client.post("/admin/kb/assets", files={"file": (filename, data, mime)})

    def test_upload_valid_returns_ready(self):
        r = self._upload()
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["status"], "ready")
        self.assertEqual(body["render_ref"], f"/assets/{body['id']}/display")

    def test_upload_unsupported_mime_rejected(self):
        r = self._upload(data=b"%PDF-1.4", mime="application/pdf", filename="x.pdf")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["detail"]["reason"], ia.REASON_UNSUPPORTED_MIME)
        # a rejected row is persisted for audit
        row = self.db.query(schema.ImageAsset).filter(schema.ImageAsset.status == "rejected").first()
        self.assertIsNotNone(row)

    def test_upload_undecodable_failed(self):
        r = self._upload(data=b"\x89PNG-broken", mime="image/png")
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json()["detail"]["reason"], ia.REASON_DECODE_FAILED)

    def test_serve_ready_variants(self):
        asset_id = self._upload().json()["id"]
        for variant, ctype in (("thumb", "image/webp"), ("display", "image/webp"), ("original", "image/png")):
            resp = self.client.get(f"/assets/{asset_id}/{variant}")
            self.assertEqual(resp.status_code, 200, variant)
            self.assertEqual(resp.headers["content-type"], ctype)

    def test_serve_non_ready_is_404(self):
        # a rejected asset must never be served (4-state gate)
        row = schema.ImageAsset(content_hash="abc", status="rejected", failure_reason="x")
        self.db.add(row)
        self.db.commit()
        self.assertEqual(self.client.get(f"/assets/{row.id}/display").status_code, 404)

    def test_serve_missing_asset_404(self):
        self.assertEqual(self.client.get("/assets/99999/display").status_code, 404)

    def test_admin_status_and_list(self):
        asset_id = self._upload().json()["id"]
        self.assertEqual(self.client.get(f"/admin/kb/assets/{asset_id}").json()["status"], "ready")
        self.assertGreaterEqual(len(self.client.get("/admin/kb/assets").json()), 1)

    def test_upload_links_kb_item(self):
        item = schema.KBItem(question="Andres Bonifacio building", answer="(image)",
                             created_at=0, last_updated=0)
        self.db.add(item)
        self.db.commit()
        item_id = item.id
        r = self.client.post("/admin/kb/assets",
                             files={"file": ("x.png", _png(), "image/png")},
                             data={"kb_item_id": str(item_id)})
        self.assertEqual(r.status_code, 200)
        linked = self.db.query(schema.KBItem).filter(schema.KBItem.id == item_id).first()
        self.assertEqual(linked.image_asset_id, r.json()["id"])
        self.assertEqual(linked.modality, "image")


if __name__ == "__main__":
    unittest.main()
