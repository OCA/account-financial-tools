This module will add the purchase order line to journal items.

The ultimate goal is to establish the purchase order line as one of the key
fields to reconcile the Goods Received Not Invoiced accrual account.

Field oca_purchase_line_id it's necessary. In Odoo >=16 automatic
revaluation for a product with FIFO costing method only works if invoice
lines related to a purchase order line do not include stock journal items.
To avoid that oca_purchase_line_id includes invoice and stock journal items,
and we keep Odoo field invoice_lines just with bill lines.
- Check issue https://github.com/OCA/account-financial-tools/issues/2017
