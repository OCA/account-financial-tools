![Licence](https://img.shields.io/badge/licence-AGPL--3-blue.svg)
[![Runbot Status](https://runbot.odoo-community.org/runbot/badge/flat/92/10.0.svg)](https://runbot.odoo-community.org/runbot/repo/github-com-oca-account-financial-tools-92)
[![Build Status](https://travis-ci.org/OCA/account-financial-tools.svg?branch=10.0)](https://travis-ci.org/OCA/account-financial-tools)
[![Coverage Status](https://coveralls.io/repos/OCA/account-financial-tools/badge.svg?branch=10.0)](https://coveralls.io/r/OCA/account-financial-tools?branch=10.0)

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
addon | version | summary
--- | --- | ---
[account_asset_depr_line_cancel](account_asset_depr_line_cancel/) | 10.0.1.0.0 | Assets Management - Cancel button
[account_check_deposit](account_check_deposit/) | 10.0.1.0.0 | Manage deposit of checks to the bank
[account_fiscal_position_vat_check](account_fiscal_position_vat_check/) | 10.0.1.0.0 | Check VAT on invoice validation
[account_fiscal_year](account_fiscal_year/) | 10.0.1.0.0 | Account Fiscal Year
[account_move_line_payable_receivable_filter](account_move_line_payable_receivable_filter/) | 10.0.1.0.0 | Filter your Journal Items per payable and receivable account
[account_partner_required](account_partner_required/) | 10.0.1.0.0 | Adds an option 'partner policy' on account types
[account_permanent_lock_move](account_permanent_lock_move/) | 10.0.1.0.0 | Permanent Lock Move
[account_reversal](account_reversal/) | 10.0.1.0.0 | Wizard for creating a reversal account move
[account_type_menu](account_type_menu/) | 10.0.1.0.0 | Adds a menu entry for Account Types
[currency_rate_update](currency_rate_update/) | 10.0.1.0.0 | Currency Rate Update


Unported addons
---------------
addon | version | summary
--- | --- | ---
[account_asset_management](account_asset_management/) | 8.0.2.6.0 (unported) | Assets Management
[account_asset_management_xls](account_asset_management_xls/) | 8.0.0.1.0 (unported) | Assets Management Excel reporting
[account_balance_line](account_balance_line/) | 8.0.1.1.0 (unported) | Display balance totals in move line view
[account_cancel_invoice_check_payment_order](account_cancel_invoice_check_payment_order/) | 1.0 (unported) | Cancel invoice, check on payment order
[account_cancel_invoice_check_voucher](account_cancel_invoice_check_voucher/) | 1.0 (unported) | Cancel invoice, check on bank statement
[account_chart_update](account_chart_update/) | 8.0.1.2.0 (unported) | Detect changes and update the Account Chart from a template
[account_constraints](account_constraints/) | 8.0.1.1.0 (unported) | Account Constraints
[account_credit_control](account_credit_control/) | 8.0.0.3.0 (unported) | Account Credit Control
[account_credit_control_dunning_fees](account_credit_control_dunning_fees/) | 8.0.0.1.0 (unported) | Credit control dunning fees
[account_default_draft_move](account_default_draft_move/) | 8.0.1.0.0 (unported) | Move in draft state by default
[account_invoice_constraint_chronology](account_invoice_constraint_chronology/) | 8.0.1.0.0 (unported) | Account Invoice Constraint Chronology
[account_invoice_currency](account_invoice_currency/) | 8.0.1.0.0 (unported) | Company currency in invoices
[account_invoice_tax_required](account_invoice_tax_required/) | 8.0.1.0.0 (unported) | Tax required in invoice
[account_journal_always_check_date](account_journal_always_check_date/) | 8.0.0.1.0 (unported) | Option Check Date in Period always active on journals
[account_journal_period_close](account_journal_period_close/) | 8.0.1.0.0 (unported) | Account Journal Period Close
[account_move_batch_validate](account_move_batch_validate/) | 8.0.0.2.0 (unported) | Account Move Batch Validate
[account_move_line_no_default_search](account_move_line_no_default_search/) | 8.0.0.1.0 (unported) | Move line search view - disable defaults for period and journal
[account_move_line_search_extension](account_move_line_search_extension/) | 8.0.0.6.0 (unported) | Journal Items Search Extension
[account_move_locking](account_move_locking/) | 9.0.1.0.0 (unported) | Move locked to prevent modification
[account_move_template](account_move_template/) | 8.0.1.0.0 (unported) | Templates for recurring Journal Entries
[account_renumber](account_renumber/) | 9.0.1.0.0 (unported) | Account Renumber Wizard
[account_reset_chart](account_reset_chart/) | 8.0.1.0.0 (unported) | Delete the accounting setup from an otherwise reusable database
[account_tax_update](account_tax_update/) | 1.0.44 (unported) | Update tax wizard
[async_move_line_importer](async_move_line_importer/) | 0.1.2 (unported) | Asynchronous move/move line CSV importer
[currency_rate_date_check](currency_rate_date_check/) | 8.0.1.0.0 (unported) | Make sure currency rates used are always up-to-update

[//]: # (end addons)

Translation Status
------------------
[![Transifex Status](https://www.transifex.com/projects/p/OCA-account-financial-tools-10-0/chart/image_png)](https://www.transifex.com/projects/p/OCA-account-financial-tools-10-0)
