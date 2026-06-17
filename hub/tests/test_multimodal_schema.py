"""
hub/tests/test_multimodal_schema.py

Phase 7 / Slice 7A — multimodal KB schema (D12/D13).
Verifies the kb_items table + KBItem model + KBArticle alias, the new columns,
modality defaulting to text, backward-compatible text retrieval, and that the
evidence contract can carry modality.
"""

import unittest
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from hub.db.session import Base
from hub.db import schema
from hub.models import api_models


class TestKBItemSchema(unittest.TestCase):
    def test_table_renamed_and_alias(self):
        self.assertEqual(schema.KBItem.__tablename__, "kb_items")
        self.assertIs(schema.KBArticle, schema.KBItem)  # back-compat alias

    def test_multimodal_columns_present(self):
        cols = {c.name for c in schema.KBItem.__table__.columns}
        for c in ("modality", "image_asset_id", "parent_article_id", "segment_index", "metadata_json"):
            self.assertIn(c, cols)
        # existing text fields preserved
        for c in ("question", "answer", "category", "embedding", "authority", "scope"):
            self.assertIn(c, cols)

    def test_taxonomy_fk_targets_kb_items(self):
        fk = list(schema.KBItemTaxonomy.__table__.c.kb_item_id.foreign_keys)[0]
        self.assertEqual(fk.column.table.name, "kb_items")

    def test_migration_has_multimodal_alters(self):
        src = (Path(schema.__file__).parent / "migrate_schema.py").read_text(encoding="utf-8")
        for c in ("modality", "image_asset_id", "parent_article_id", "segment_index", "metadata_json"):
            self.assertIn(f"ADD COLUMN {c}", src)


class TestModalityBehavior(unittest.TestCase):
    def setUp(self):
        e = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(e)  # builds kb_items
        self.db = sessionmaker(bind=e)()

    def tearDown(self):
        self.db.close()

    def test_text_item_defaults_and_roundtrips(self):
        item = schema.KBItem(question="Where is food?", answer="Hall A", category="food",
                             enabled=1, created_at=0, last_updated=0)
        self.db.add(item)
        self.db.commit()
        row = self.db.query(schema.KBItem).first()
        self.assertEqual(row.question, "Where is food?")
        # modality defaults to text; image fields null for text rows
        self.assertEqual(row.modality, "text")
        self.assertIsNone(row.image_asset_id)
        self.assertIsNone(row.parent_article_id)

    def test_image_item_representable(self):
        item = schema.KBItem(question="Andres Bonifacio building", answer="(image)",
                             modality="image", image_asset_id=99, created_at=0, last_updated=0)
        self.db.add(item)
        self.db.commit()
        row = self.db.query(schema.KBItem).filter(schema.KBItem.modality == "image").first()
        self.assertEqual(row.image_asset_id, 99)


class TestEvidenceContractModality(unittest.TestCase):
    def test_queryresponse_has_modality(self):
        r = api_models.QueryResponse(answer_text_en="x", answer_type="DIRECT_MATCH",
                                     confidence=0.9, kb_version=1)
        self.assertEqual(r.modality, "text")  # default
        self.assertIsNone(r.render_ref)

    def test_secondary_evidence_has_modality(self):
        s = api_models.SecondaryEvidence(intent="location", source_id=5, modality="image")
        self.assertEqual(s.modality, "image")


if __name__ == "__main__":
    unittest.main()
