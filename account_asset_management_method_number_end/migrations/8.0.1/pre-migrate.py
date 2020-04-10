# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate(cr, version):

    # remove translation so that field label & help is reloaded
    cr.execute(
        "DELETE FROM ir_translation "
        "WHERE module LIKE 'account_asset%' "
        "AND src ILIKE '%number of years%' "
        "AND name LIKE 'account.asset.%';")
