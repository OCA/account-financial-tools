# -*- coding: utf-8 -*-
# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp.addons.account_block_account.tests.test_account_block_account \
    import TestAccountBlockAccount as _TestAccountBlockAccount


def TestAccountBlockCostCenter(_TestAccountBlockAccount):
    def test_account_block_account(self):
        return super(
            TestAccountBlockCostCenter, self
        ).test_account_block_account()
