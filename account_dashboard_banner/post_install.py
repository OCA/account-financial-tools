# Copyright 2025 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# I create default cells via post-install script instead of
# data/account_dashboard_banner_cell.xml
# to avoid the problem when a user deletes a cell that has an XMLID
# and Odoo would re-create the cells when the module is reloaded
def create_default_account_dashboard_cells(env):
    vals_list = [
        {"cell_type": "hard_lock_date", "sequence": 10, "warn": True},
        {"cell_type": "income_fiscalyear", "sequence": 20},
        {"cell_type": "customer_overdue", "sequence": 30},
        {"cell_type": "customer_debt", "sequence": 40},
        {"cell_type": "supplier_debt", "sequence": 50},
        {"cell_type": "liquidity", "sequence": 60, "warn": True, "warn_type": "under"},
    ]
    env["account.dashboard.banner.cell"].create(vals_list)
