Prevent automatically reconciliation when invoicing a stock move or when validating
a stock move.
When receiving in multiple incoming shipments and invoicing periodically,
it is not desirable to reconcile until the order (SO/PO) is closed, otherwise you can get
an error when receiving or delivering another pickng, because of the partial reconcile
https://github.com/odoo/odoo/blob/15.0/addons/account/models/account_move.py#L4463

You can use additional modules, like purchase_unreconciled and sale_unreconciled in
order to perform the reconciliation when the order is fully done.

Technically, this does not depend on purchase and sale, but the symptoms only appear
when the invoce is linked to a PO SO.
