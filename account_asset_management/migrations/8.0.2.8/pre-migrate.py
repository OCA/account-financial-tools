# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate(cr, version):

    # rename colums
    cr.execute(
        "SELECT column_name "
        "FROM information_schema.columns "
        "WHERE table_name='account_asset_asset' "
        "AND column_name='depreciation_base';")
    res = cr.fetchone()
    if not res:
        cr.execute(
            "ALTER TABLE account_asset_asset "
            "RENAME asset_value TO depreciation_base;")
        cr.execute(
            "UPDATE ir_model_fields "
            "SET name='depreciation_base', "
            "field_description='Depreciation Base' "
            "WHERE model='account.asset.asset' AND name='asset_value';")
        cr.execute(
            "UPDATE ir_model_data "
            "SET name='field_account_asset_asset_depreciation_base' "
            "WHERE model='ir.model.fields' "
            "AND name='field_account_asset_asset_asset_value';")

    # set values on 'view' assets to 0.0
    cr.execute(
        "update account_asset_asset "
        "SET value_residual = 0.0, value_depreciated = 0.0, "
        "depreciation_base = 0.0 "
        "WHERE type = 'view'")
