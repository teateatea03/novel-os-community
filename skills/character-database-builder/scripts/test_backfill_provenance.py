#!/usr/bin/env python3
"""Backfilled placeholders must not claim a fabricated verification date."""
import unittest
import backfill_minimum_character_cards as backfill


class BackfillProvenanceTests(unittest.TestCase):
    def test_generated_cards_are_explicitly_unverified(self):
        node = {"id": "synthetic-technician", "label": "示例技術員"}
        cases = (
            (backfill.ship_card, {"ship_type": "運輸"}),
            (backfill.public_card, {"public_roles": "公開科學展覽講解"}),
            (backfill.public_card, {}),
            (backfill.fictional_card, {"role": "虛構觀測站技術員"}),
        )
        for factory, properties in cases:
            with self.subTest(factory=factory.__name__, properties=properties):
                card = factory(node, properties)
                self.assertEqual(card["last_verified"], "UNKNOWN")
                self.assertEqual(card["verification_status"], "not_independently_verified")


if __name__ == "__main__":
    unittest.main()
