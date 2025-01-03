This module enables by default the setting *Lock Posted Entries with
Hash* in all Sales, Purchase and Miscellaneous Journals, and prevents
the setting to be modified.

The goal is to assure that all journal entries are locked when posted to
prevent them to be modified.

Bank and Cash journals can't be hashed as it conflicts with Odoo's logic when
creating bank transactions (https://github.com/odoo/odoo/commit/9740189bc59658a62da6a624e166505841ac30a4).
