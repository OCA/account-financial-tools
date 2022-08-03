
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/account-financial-tools&target_branch=13.0)
[![Pre-commit Status](https://github.com/OCA/account-financial-tools/actions/workflows/pre-commit.yml/badge.svg?branch=13.0)](https://github.com/OCA/account-financial-tools/actions/workflows/pre-commit.yml?query=branch%3A13.0)
[![Build Status](https://github.com/OCA/account-financial-tools/actions/workflows/test.yml/badge.svg?branch=13.0)](https://github.com/OCA/account-financial-tools/actions/workflows/test.yml?query=branch%3A13.0)
[![codecov](https://codecov.io/gh/OCA/account-financial-tools/branch/13.0/graph/badge.svg)](https://codecov.io/gh/OCA/account-financial-tools)
[![Translation Status](https://translation.odoo-community.org/widgets/account-financial-tools-13-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/account-financial-tools-13-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# Account Financial Tools

Account financial Tools for Odoo/OpenERP

This project aims to make the accounting usage system easy and painless.
It provides addons to:

 - Update the currency rate automatically via web services
 - Push credit management and follow up to next level
 - Generate reversed account moves
 - Cancel invoices with ease
 - Force draft accounting by default
 - Enforce partners on account moves

And much more.

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[account_asset_batch_compute](account_asset_batch_compute/) | 13.0.1.0.0 |  | Add the possibility to compute assets in batch
[account_asset_management](account_asset_management/) | 13.0.3.7.3 |  | Assets Management
[account_asset_management_menu](account_asset_management_menu/) | 13.0.1.0.0 |  | Assets Management Menu
[account_balance_line](account_balance_line/) | 13.0.1.0.0 |  | Display balance totals in move line view
[account_cash_basis_group_base_line](account_cash_basis_group_base_line/) | 13.0.0.0.1 |  | Compacting the creation of Journal Lines for CABA base lines.
[account_chart_update](account_chart_update/) | 13.0.2.0.1 |  | Wizard to update a company's account chart from a template
[account_check_deposit](account_check_deposit/) | 13.0.1.2.0 |  | Manage deposit of checks to the bank
[account_document_reversal](account_document_reversal/) | 13.0.1.0.0 | [![kittiu](https://github.com/kittiu.png?size=30px)](https://github.com/kittiu) | Create reversed journal entries when cancel document
[account_fiscal_month](account_fiscal_month/) | 13.0.1.0.0 |  | Provide a fiscal month date range type
[account_fiscal_position_allowed_journal](account_fiscal_position_allowed_journal/) | 13.0.1.0.0 | [![ThomasBinsfeld](https://github.com/ThomasBinsfeld.png?size=30px)](https://github.com/ThomasBinsfeld) | Allow defining allowed journals on fiscal positions. Related invoices can only use one of the allowed journals on the fiscal position.
[account_fiscal_year](account_fiscal_year/) | 13.0.1.0.0 | [![eLBati](https://github.com/eLBati.png?size=30px)](https://github.com/eLBati) | Create a menu for Account Fiscal Year
[account_invoice_constraint_chronology](account_invoice_constraint_chronology/) | 13.0.1.0.2 |  | Account Invoice Constraint Chronology
[account_journal_lock_date](account_journal_lock_date/) | 13.0.1.0.0 |  | Lock each journal independently
[account_loan](account_loan/) | 13.0.1.1.0 |  | Account Loan management
[account_lock_date_update](account_lock_date_update/) | 13.0.1.0.0 |  | Allow an Account adviser to update locking date without having access to all technical settings
[account_lock_to_date](account_lock_to_date/) | 13.0.1.0.1 |  | Allows to set an account lock date in the future.
[account_maturity_date_default](account_maturity_date_default/) | 13.0.2.0.0 | [![victoralmau](https://github.com/victoralmau.png?size=30px)](https://github.com/victoralmau) | Account Maturity Date Default
[account_menu](account_menu/) | 13.0.1.0.0 |  | Adds missing menu entries for Account module
[account_move_budget](account_move_budget/) | 13.0.1.0.0 |  | Create Accounting Budgets
[account_move_force_removal](account_move_force_removal/) | 13.0.1.0.0 |  | Allow force removal account moves
[account_move_line_purchase_info](account_move_line_purchase_info/) | 13.0.1.1.3 |  | Introduces the purchase order line to the journal items
[account_move_line_sale_info](account_move_line_sale_info/) | 13.0.1.0.3 |  | Introduces the purchase order line to the journal items
[account_move_line_tax_editable](account_move_line_tax_editable/) | 13.0.2.0.0 |  | Allows to edit taxes on non-posted account move lines
[account_move_line_used_currency](account_move_line_used_currency/) | 13.0.1.0.0 |  | Account Move Line Amount Currency
[account_move_print](account_move_print/) | 13.0.1.0.0 | [![JordiBForgeFlow](https://github.com/JordiBForgeFlow.png?size=30px)](https://github.com/JordiBForgeFlow) | Adds the option to print Journal Entries
[account_move_reversal_choose_method](account_move_reversal_choose_method/) | 13.0.1.0.0 |  | Let's choose the Credit Method when adding a credit note to a journal entry.
[account_move_template](account_move_template/) | 13.0.1.2.0 |  | Templates for recurring Journal Entries
[account_netting](account_netting/) | 13.0.1.0.1 |  | Compensate AR/AP accounts from the same partner
[account_spread_cost_revenue](account_spread_cost_revenue/) | 13.0.1.0.1 | [![astirpe](https://github.com/astirpe.png?size=30px)](https://github.com/astirpe) | Spread costs and revenues over a custom period
[account_tax_repartition_line_tax_group_account](account_tax_repartition_line_tax_group_account/) | 13.0.1.0.0 |  | Set a default account from tax group to tax repartition lines
[base_vat_optional_vies](base_vat_optional_vies/) | 13.0.1.0.1 |  | Optional validation of VAT via VIES
[product_category_tax](product_category_tax/) | 13.0.1.2.0 |  | Configure taxes in the product category
[stock_account_prepare_anglo_saxon_out_lines_hook](stock_account_prepare_anglo_saxon_out_lines_hook/) | 13.0.1.0.3 |  | Modify when and how anglo saxon journal items are created

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to Odoo Community Association (OCA)
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.
