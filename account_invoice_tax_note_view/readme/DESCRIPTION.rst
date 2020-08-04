Two OCA modules are present and both depends on account,

account_invoice_tax_note

- adding a tax group note on account.tax.group model
  but does not add a field to view, because it depends on account module,
  whic1h by default has no account.tax.group views defined

- default odoo form and tree views are generated "on the fly" and added
  field "note" is visible and editale on form view.


account_group_menu

- adds missing menuitems and defines views for account tax group
  but is not aware of any extensions or added fields.

This module is connector between those two and adds a field to form view so
users won't be confused with field not visible after module instalation.

To contribute to this module, please visit https://odoo-community.org.
