# Copyright 2021 Opener B.V. <stefan@opener.amsterdam>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from odoo import models


class AccountGroup(models.Model):
    _inherit = "account.group"

    def _parent_store_update(self):
        """Propagated the updated parent structure to accounts and move lines
        """
        res = super()._parent_store_update()
        if self:
            self._account_groups_compute()
        return res

    def _account_groups_compute(self):
        """Set root and sub groups on accounts and move lines.

        Can be called on a recordset of account.group or with an empty `self`
        to apply on all accounts with a group_id set.

        Only rewrite the move lines of the updated accounts, and take care
        not to select accounts that already have the current values set.
        """
        self.env.cr.execute(
            """
            WITH vals AS (
                SELECT aa.id,
                CAST(split_part(ag.parent_path, '/', 1) AS INTEGER)
                    as root_group_id,
                CASE
                    WHEN length(split_part(parent_path, '/', 2)) > 0
                    THEN CAST(split_part(parent_path, '/', 2) AS INTEGER)
                    ELSE NULL END AS sub_group_id
                FROM account_account aa
                JOIN account_group ag ON ag.id = aa.group_id
            """ + (" WHERE ag.id IN %s " if self.ids else "") +
            """
            )
            UPDATE account_account aa
            SET root_group_id = vals.root_group_id,
                sub_group_id = vals.sub_group_id
            FROM vals
            WHERE aa.id = vals.id
            AND (
                COALESCE(aa.root_group_id, 0) !=
                COALESCE(vals.root_group_id, 0)
                OR
                COALESCE(aa.sub_group_id, 0) !=
                COALESCE(vals.sub_group_id, 0)
            )
            RETURNING aa.id;
            """,
            (tuple(self.ids),) if self.ids else ())
        account_ids = [account_id for account_id, in self.env.cr.fetchall()]
        if not account_ids:
            return
        logging.getLogger(__name__).debug(
            "Recomputing the root and sub groups of all move lines of %s "
            "account(s).", len(account_ids))
        self.env.cr.execute(
            """
            UPDATE account_move_line aml
            SET account_root_group_id = aa.root_group_id,
                account_sub_group_id = aa.sub_group_id
            FROM account_account aa
            WHERE aml.account_id = aa.id
                AND aa.id IN %s
            """, (tuple(account_ids),))
        self.env.cache.invalidate([
            (self.env["account.account"]._fields['root_group_id'], None),
            (self.env["account.account"]._fields['sub_group_id'], None),
            (self.env["account.move.line"]._fields['account_root_group_id'],
             None),
            (self.env["account.move.line"]._fields['account_sub_group_id'],
             None),
        ])
