# -*- coding: utf-8 -*-
# Copyright Stephane LE CORNEC
# Copyright 2017 Tecnativa - Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2017 Tecnativa - Luis M. Ontalba <luis.martinez@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


def cleanup_modules(cr):
    """Don't report as missing these modules, as they are integrated in
    other modules."""
    openupgrade.update_module_names(
        cr, [
            ('account_asset_disposal_analytic', 'account_asset_analytic'),
        ], merge_modules=True,
    )


@openupgrade.migrate()
def migrate(cr, version):
    cleanup_modules(cr)
