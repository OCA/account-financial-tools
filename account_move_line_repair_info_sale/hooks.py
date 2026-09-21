# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def post_init_hook(env):
    """Back-fill repair_order_id on invoice AMLs linked to repairs via SOs.
    If a Sale Order is linked to more than one Repair Order
    (that should not be the case), the UPDATE will
    write whichever row Postgres returns first
    """
    env.cr.execute(
        """
        UPDATE account_move_line aml
           SET repair_order_id = ro.id
          FROM sale_order_line_invoice_rel rel
          JOIN sale_order_line sol ON sol.id           = rel.order_line_id
          JOIN sale_order      so  ON so.id            = sol.order_id
          JOIN repair_order    ro  ON ro.sale_order_id = so.id
         WHERE aml.id              = rel.invoice_line_id
           AND aml.move_id         IN (
                   SELECT id FROM account_move
                    WHERE move_type IN ('out_invoice', 'out_refund')
               )
           AND aml.repair_order_id IS NULL;
        """
    )
