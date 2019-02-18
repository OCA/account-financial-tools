# Copyright 2016 Jairo Llopis <jairo.llopis@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date
from odoo import exceptions, fields
from odoo.tests.common import TransactionCase


class AccountRenumberCase(TransactionCase):
    def setUp(self):
        super(AccountRenumberCase, self).setUp()
        self.today = date.today()

        self.accounts = self.env["account.account"]
        for n in range(2):
            self.accounts |= self.accounts.create({
                "name": "Account %d" % n,
                "code": "lalala%d" % n,
                "user_type_id":
                    self.env.ref("account.data_account_type_liquidity").id,
            })

        self.sequence = self.env["ir.sequence"].create({
            "name": "Test Sëquence",
            "implementation": "no_gap",
            "prefix": "TEST/%(year)s/",
            "use_date_range": True,
        })

        self.date_range = self.env["ir.sequence.date_range"].create({
            "date_from": date(self.today.year, 1, 1),
            "date_to": date(self.today.year, 12, 31),
            "sequence_id": self.sequence.id,
        })

        self.journal = self.env["account.journal"].create({
            "name": "Test Jöurnal",
            "type": "cash",
            "sequence_id": self.sequence.id,
        })

        # Create some dummy accounting entries
        moves = self.env["account.move"]
        for n in range(9):
            move = moves.create({
                "ref": "Test %s" % n,
                "journal_id": self.journal.id,
                "date": date(self.today.year, 12 - n, 1),
                "line_ids": [
                    (0, False, {
                        "account_id": self.accounts[0].id,
                        "name": "Line %d.1" % n,
                        "debit": 100,
                    }),
                    (0, False, {
                        "account_id": self.accounts[1].id,
                        "name": "Line %d.2" % n,
                        "credit": 100,
                    }),
                ],
            })
            move.post()
            moves |= move

        # Get them sorted by default order
        self.moves = moves.search([("id", "in", moves.ids)])

    def moves_by_name(self, moves):
        """Search moves sorted by name (move number, inversed)."""
        return moves.search(
            [("id", "in", moves.ids)],
            order="name desc")

    def test_renumber_all(self):
        """All moves are renumbered."""
        wizard = self.env["wizard.renumber"].create({
            "date_to": date(self.today.year, 12, 31),
        })
        wizard.journal_ids = self.journal
        wizard.renumber()
        new_moves = self.moves_by_name(self.moves)
        for n, move in enumerate(self.moves):
            self.assertEqual(move, new_moves[n])

    def test_renumber_only_one_journal(self):
        """Only moves from one journal are renumbered."""
        new_journal = self.journal.copy()
        self.moves[:4].write({"journal_id": new_journal.id})
        wizard = self.env["wizard.renumber"].create({
            "date_to": date(self.today.year, 12, 31),
        })
        wizard.journal_ids = self.journal
        renumbered_ids = wizard.renumber()["domain"][0][2]

        for move in self.moves[:4]:
            self.assertNotIn(move.id, renumbered_ids)
        for move in self.moves[4:]:
            self.assertIn(move.id, renumbered_ids)

    def test_renumber_half_year(self):
        """Only moves from the second half of the year are renumbered."""
        date_from = fields.Date.to_string(date(self.today.year, 7, 1))
        wizard = self.env["wizard.renumber"].create({
            "date_from": date_from,
            "date_to": date(self.today.year, 12, 31),
        })
        wizard.journal_ids = self.journal
        wizard.renumber()

        expected_month = list(range(4, 7)) + list(range(12, 6, -1))
        expected_number = list(range(9, 0, -1))
        for n, move in enumerate(self.moves_by_name(self.moves)):
            self.assertEqual(int(move.name[-1]), expected_number[n])
            self.assertEqual(
                fields.Date.from_string(move.date).month,
                expected_month[n])

    def test_renumber_all_no_date_ranges_in_sequence(self):
        """Works fine using a sequence without date ranges."""
        self.sequence.use_date_range = False
        self.test_renumber_all()

    def test_failure_when_no_results(self):
        """Ensure an exception is raised when no results are found."""
        new_journal = self.journal.copy()
        self.moves.write({"journal_id": new_journal.id})
        with self.assertRaises(exceptions.MissingError):
            self.test_renumber_all()
