"""hub/tests/test_response_cache.py — Phase 6 safe response cache (D10/D11)."""

import unittest

from hub.retrieval import response_cache as rc


class TestConfigSignature(unittest.TestCase):
    def test_stable_and_short(self):
        a = rc.build_config_signature()
        b = rc.build_config_signature()
        self.assertEqual(a, b)
        self.assertTrue(0 < len(a) <= 12)

    def test_changes_when_config_changes(self):
        import hub.retrieval.search as search
        base = rc.build_config_signature()
        orig = search.THRESHOLD
        try:
            search.THRESHOLD = orig + 0.05
            self.assertNotEqual(rc.build_config_signature(), base)
        finally:
            search.THRESHOLD = orig
        self.assertEqual(rc.build_config_signature(), base)


class TestSafety(unittest.TestCase):
    def test_safety_intents(self):
        for i in ("safety", "emergency", "medical", "children", "special_needs"):
            self.assertTrue(rc.is_safety_critical(i))
        for i in ("food", "location", "registration", None):
            self.assertFalse(rc.is_safety_critical(i))


class TestCache(unittest.TestCase):
    def setUp(self):
        rc.invalidate_response_cache()

    def _key(self, **over):
        base = dict(normalized_query="where is food", intent="food", language="en",
                    ui_filter=None, exclude_ids=None, kb_version=1, config_signature="cfg")
        base.update(over)
        return rc.make_cache_key(**base)

    def test_miss_then_hit(self):
        k = self._key()
        self.assertIsNone(rc.get(k, now=1000))
        rc.set(k, {"answer": "Hall A"}, now=1000)
        self.assertEqual(rc.get(k, now=1001), {"answer": "Hall A"})

    def test_kb_version_changes_key(self):
        self.assertNotEqual(self._key(kb_version=1), self._key(kb_version=2))

    def test_config_signature_changes_key(self):
        self.assertNotEqual(self._key(config_signature="a"), self._key(config_signature="b"))

    def test_filter_changes_key(self):
        self.assertNotEqual(self._key(ui_filter=None), self._key(ui_filter="rk.tax.food"))
        self.assertNotEqual(self._key(exclude_ids=[1]), self._key(exclude_ids=[2]))

    def test_ttl_expiry(self):
        k = self._key()
        rc.set(k, {"a": 1}, now=1000, ttl=300)
        self.assertIsNotNone(rc.get(k, now=1299))
        self.assertIsNone(rc.get(k, now=1300))  # expired at now>=expires_at

    def test_ttl_zero_disables(self):
        k = self._key()
        rc.set(k, {"a": 1}, now=1000, ttl=0)
        self.assertIsNone(rc.get(k, now=1000))

    def test_invalidate_clears(self):
        k = self._key()
        rc.set(k, {"a": 1}, now=1000)
        rc.invalidate_response_cache()
        self.assertIsNone(rc.get(k, now=1000))

    def test_lru_eviction(self):
        orig = rc.MAX_ENTRIES
        rc.MAX_ENTRIES = 3
        try:
            for i in range(4):
                rc.set(self._key(normalized_query=f"q{i}"), {"i": i}, now=1000)
            # only 3 kept; the first inserted (q0) evicted
            self.assertEqual(rc.stats()["size"], 3)
            self.assertIsNone(rc.get(self._key(normalized_query="q0"), now=1000))
            self.assertIsNotNone(rc.get(self._key(normalized_query="q3"), now=1000))
        finally:
            rc.MAX_ENTRIES = orig


if __name__ == "__main__":
    unittest.main()
