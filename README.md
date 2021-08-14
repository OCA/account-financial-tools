![Licence](https://img.shields.io/badge/licence-AGPL--3-blue.svg)
[![Runbot Status](https://runbot.odoo-community.org/runbot/badge/flat/92/9.0.svg)](https://runbot.odoo-community.org/runbot/repo/github-com-oca-account-financial-tools-92)
[![Build Status](https://travis-ci.org/OCA/account-financial-tools.svg?branch=9.0)](https://travis-ci.org/OCA/account-financial-tools)
[![Coverage Status](https://coveralls.io/repos/OCA/account-financial-tools/badge.svg?branch=9.0)](https://coveralls.io/r/OCA/account-financial-tools?branch=9.0)

Account financial Tools for Odoo/OpenERP
========================================

This project aims to make the accounting usage system easy and painless.
It provides addons to:

 - Update the currency rate automatically via web services
 - Push credit management and follow up to next level
 - Generate reversed account moves
 - Cancel invoices with ease
 - Force draft accounting by default
 - Enforce partners on account moves

And much more.

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[account_asset_depr_line_cancel](account_asset_depr_line_cancel/) | 9.0.1.0.0 |  | Assets Management - Cancel button
[account_balance_line](account_balance_line/) | 9.0.1.1.0 |  | Display balance totals in move line view
[account_chart_update](account_chart_update/) | 9.0.1.0.1 |  | Wizard to update a company's account chart from a template
[account_check_deposit](account_check_deposit/) | 9.0.0.1.0 |  | Manage deposit of checks to the bank
[account_cost_center](account_cost_center/) | 9.0.1.0.0 |  | Cost center information for invoice lines
[account_credit_control](account_credit_control/) | 9.0.1.0.4 |  | Account Credit Control
[account_fiscal_position_vat_check](account_fiscal_position_vat_check/) | 9.0.1.0.0 |  | Check VAT on invoice validation
[account_fiscal_year](account_fiscal_year/) | 9.0.1.0.0 |  | Account Fiscal Year
[account_invoice_currency](account_invoice_currency/) | 9.0.1.0.0 |  | Company currency in invoices
[account_invoice_tax_required](account_invoice_tax_required/) | 9.0.1.0.0 |  | Tax required in invoice
[account_move_line_purchase_info](account_move_line_purchase_info/) | 9.0.1.0.0 |  | Introduces the purchase order line to the journal items
[account_move_locking](account_move_locking/) | 9.0.1.0.0 |  | Move locked to prevent modification
[account_permanent_lock_move](account_permanent_lock_move/) | 9.0.1.0.0 |  | Permanent Lock Move
[account_renumber](account_renumber/) | 9.0.1.0.1 |  | Account Renumber Wizard
[account_reversal](account_reversal/) | 9.0.1.0.0 |  | Wizard for creating a reversal account move
[currency_rate_update](currency_rate_update/) | 9.0.1.0.0 |  | Currency Rate Update


Unported addons
---------------
addon | version | maintainers | summary
--- | --- | --- | ---
[account_asset_management](account_asset_management/) | 8.0.2.6.0 (unported) |  | Assets Management
[account_cancel_invoice_check_payment_order](account_cancel_invoice_check_payment_order/) | 1.0 (unported) |  | Cancel invoice, check on payment order
[account_cancel_invoice_check_voucher](account_cancel_invoice_check_voucher/) | 1.0 (unported) |  | Cancel invoice, check on bank statement
[account_constraints](account_constraints/) | 8.0.1.1.0 (unported) |  | Account Constraints
[account_credit_control_dunning_fees](account_credit_control_dunning_fees/) | 8.0.0.1.0 (unported) |  | Credit control dunning fees
[account_default_draft_move](account_default_draft_move/) | 8.0.1.0.0 (unported) |  | Move in draft state by default
[account_invoice_constraint_chronology](account_invoice_constraint_chronology/) | 8.0.1.0.0 (unported) |  | Account Invoice Constraint Chronology
[account_journal_always_check_date](account_journal_always_check_date/) | 8.0.0.1.0 (unported) |  | Option Check Date in Period always active on journals
[account_journal_period_close](account_journal_period_close/) | 8.0.1.0.0 (unported) |  | Account Journal Period Close
[account_move_batch_validate](account_move_batch_validate/) | 8.0.0.2.0 (unported) |  | Account Move Batch Validate
[account_move_line_no_default_search](account_move_line_no_default_search/) | 8.0.0.1.0 (unported) |  | Move line search view - disable defaults for period and journal
[account_move_line_payable_receivable_filter](account_move_line_payable_receivable_filter/) | 8.0.1.0.0 (unported) |  | Filter your Journal Items per payable and receivable account
[account_move_line_search_extension](account_move_line_search_extension/) | 8.0.0.6.0 (unported) |  | Journal Items Search Extension
[account_move_template](account_move_template/) | 8.0.1.0.0 (unported) |  | Templates for recurring Journal Entries
[account_partner_required](account_partner_required/) | 8.0.0.1.0 (unported) |  | Account partner required
[account_reset_chart](account_reset_chart/) | 8.0.1.0.0 (unported) |  | Delete the accounting setup from an otherwise reusable database
[account_tax_analysis](account_tax_analysis/) | 8.0.1.0.0 (unported) |  | Tax analysis
[account_tax_chart_interval](account_tax_chart_interval/) | 8.0.1.0.0 (unported) |  | Tax chart for a period interval
[account_tax_update](account_tax_update/) | 9.0.1.0.45 (unported) |  | Update tax wizard
[async_move_line_importer](async_move_line_importer/) | 0.1.2 (unported) |  | Asynchronous move/move line CSV importer
[currency_rate_date_check](currency_rate_date_check/) | 8.0.1.0.0 (unported) |  | Make sure currency rates used are always up-to-update

[//]: # (end addons)

Translation Status
------------------
[![Transifex Status](https://www.transifex.com/projects/p/OCA-account-financial-tools-9-0/chart/image_png)](https://www.transifex.com/projects/p/OCA-account-financial-tools-9-0)
