# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def post_init_hook(env):
    # Material consumed on repair and product repaired.
    # A valuation entry may gather several stock moves, so only the entries
    # coming from a single repair order can be safely linked.
    env.cr.execute(
        """
    update account_move_line as aml set repair_order_id = q.repair_id
    from (
        select sm.account_move_id as move_id, min(sm.repair_id) as repair_id
        from stock_move as sm
        where sm.account_move_id is not null
        group by sm.account_move_id
        having count(distinct sm.repair_id) = 1
            and count(*) = count(sm.repair_id)
    ) as q
    where aml.move_id = q.move_id
    """
    )
