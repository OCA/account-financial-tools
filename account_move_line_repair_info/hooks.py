# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def post_init_hook(env):
    # Material consumed on repair
    env.cr.execute(
        """
    update account_move_line as aml set repair_order_id = q.order_id
    from (
        select aml.id, ro.id as order_id
        from account_move_line as aml
        left join account_move as am on am.id = aml.move_id
        left join stock_valuation_layer svl on svl.account_move_id = am.id
        left join stock_move as sm on sm.id = svl.stock_move_id
        left join repair_order as ro on sm.repair_id = ro.id
        where ro.id is not null
    ) as q
    where q.id = aml.id
    """
    )

    # Product Repaired
    env.cr.execute(
        """
    update account_move_line as aml set repair_order_id = q.order_id
    from (
        select aml.id, ro.id as order_id
        from account_move_line as aml
        left join account_move as am on am.id = aml.move_id
        left join stock_valuation_layer svl on svl.account_move_id = am.id
        left join stock_move as sm on sm.id = svl.stock_move_id
        left join repair_order as ro on sm.id = ro.move_id
        where ro.id is not null
    ) as q
    where q.id = aml.id
    """
    )
