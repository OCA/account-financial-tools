# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestJournalPreference(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(
            cls.env,
            login="journal_preferences",
            groups="account.group_account_invoice",
            company_id=cls.env.company.id,
            company_ids=[Command.set(cls.env.company.ids)],
        )
        cls.journals = cls.env["account.journal"].create(
            [
                {
                    "name": name,
                    "code": code,
                    "type": "general",
                    "sequence": sequence,
                    "company_id": cls.env.company.id,
                }
                for name, code, sequence in [
                    ("Preference A", "PRA", 1),
                    ("Preference B", "PRB", 2),
                    ("Preference C", "PRC", 3),
                ]
            ]
        )
        cls.domain = [("id", "in", cls.journals.ids)]
        cls.journal_model = cls.env["account.journal"].with_user(cls.user)

    def _set_preferences(self):
        self.user.with_user(self.user).write(
            {
                "preferred_journal_ids": [
                    Command.create({"journal_id": self.journals[2].id, "sequence": 1}),
                    Command.create({"journal_id": self.journals[0].id, "sequence": 2}),
                ],
            }
        )

    def test_order_domain_and_pagination(self):
        self.assertEqual(self.journal_model.search(self.domain).ids, self.journals.ids)
        self._set_preferences()
        expected = self.journals[2] | self.journals[0] | self.journals[1]
        self.assertEqual(self.journal_model.search(self.domain).ids, expected.ids)
        choices = self.journal_model.name_search(args=self.domain, limit=2)
        self.assertEqual(
            [journal_id for journal_id, _name in choices], expected[:2].ids
        )
        self.assertEqual(
            self.journal_model.search(self.domain, offset=1, limit=1).ids,
            expected[1:2].ids,
        )
        domain = self.domain + [("id", "!=", self.journals[2].id)]
        self.assertEqual(
            self.journal_model.search(domain).ids,
            (self.journals[0] | self.journals[1]).ids,
        )
        self.assertEqual(
            self.journal_model.search(self.domain, order="name desc").ids,
            list(reversed(self.journals.ids)),
        )
        self.assertEqual(self.journal_model.search_count(self.domain), 3)
        self.assertEqual(
            self.journal_model.search(self.domain, order=self.journal_model._order).ids,
            expected.ids,
        )
        self.assertFalse(self.journal_model.search([("id", "=", 0)]))

    def test_search_default_journal_uses_preferences(self):
        self._set_preferences()
        move = (
            self.env["account.move"]
            .with_user(self.user)
            .new(
                {
                    "move_type": "entry",
                    "company_id": self.env.company.id,
                    "currency_id": self.env.company.currency_id.id,
                }
            )
        )
        # C wins despite its journal sequence being higher than A's.
        self.assertEqual(move._search_default_journal().ids, self.journals[2].ids)
        first_preference = self.user.preferred_journal_ids.filtered(
            lambda preference: preference.journal_id == self.journals[2]
        )
        self.user.with_user(self.user).write(
            {"preferred_journal_ids": [Command.unlink(first_preference.id)]}
        )
        self.assertEqual(move._search_default_journal().ids, self.journals[0].ids)

    def test_preferences_can_be_disabled(self):
        self._set_preferences()
        expected = self.journals[2] | self.journals[0] | self.journals[1]
        self.assertEqual(self.journal_model.search(self.domain).ids, expected.ids)
        user = self.user.with_user(self.user)
        preferences = user.preferred_journal_ids
        user.write({"use_preferred_journals": False})
        self.assertEqual(self.journal_model.search(self.domain).ids, self.journals.ids)
        self.assertEqual(user.preferred_journal_ids.ids, preferences.ids)
        choices = self.journal_model.name_search(args=self.domain, limit=1)
        self.assertEqual(
            [journal_id for journal_id, _name in choices], self.journals[0].ids
        )
        user.write({"use_preferred_journals": True})
        self.assertEqual(self.journal_model.search(self.domain).ids, expected.ids)

    def test_preferences_are_private(self):
        self._set_preferences()
        other = new_test_user(
            self.env, login="other_preferences", groups="base.group_user"
        )
        preference = self.user.preferred_journal_ids[0]
        with self.assertRaises(AccessError):
            preference.with_user(other).write({"sequence": 99})
        self.assertFalse(
            self.env["account.journal.user.preferred"].with_user(other).search([])
        )
