# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class ReportStockMoveForecat(models.Model):
    _name = 'report.stock.move.forecast'
    _auto = False

    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    product_uom_qty = fields.Float(string='Initial Quantity', readonly=True)
    quantity = fields.Float(string='Available Quantity', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_stock_forecast')
        self._cr.execute("""CREATE or REPLACE VIEW report_stock_move_forecast AS (SELECT min(sm.id) AS id,
    sm.product_id,
    sum(COALESCE(sf.quantity, 0.0::double precision)) AS quantity,
    sum(sm.product_uom_qty) AS product_uom_qty
   FROM stock_move sm
     LEFT JOIN product_product pp ON sm.product_id = pp.id
     LEFT JOIN ( SELECT sqp.product_id,
            sum(sqp.quantity) AS quantity
           FROM stock_quant sqp
          GROUP BY sqp.product_id
          ORDER BY sqp.product_id) sqq ON sm.product_id = sqq.product_id
     LEFT JOIN ( SELECT min(final.id) AS id,
            final.product_id,
            final.date,
            sum(final.product_qty) AS quantity,
            sum(sum(final.product_qty)) OVER (PARTITION BY final.product_id ORDER BY final.date) AS cumulative_quantity
           FROM ( SELECT min(main.id) AS id,
                    main.product_id,
                    sub.date,
                        CASE
                            WHEN main.date = sub.date THEN sum(main.product_qty)
                            ELSE 0::double precision
                        END AS product_qty
                   FROM ( SELECT min(sq.id) AS id,
                            sq.product_id,
                            date_trunc('week'::text, to_date(to_char(CURRENT_DATE::timestamp with time zone, 'YYYY/MM/DD'::text), 'YYYY/MM/DD'::text)::timestamp with time zone) AS date,
                            sum(sq.quantity) AS product_qty
                           FROM stock_quant sq
                             LEFT JOIN product_product ON product_product.id = sq.product_id
                             LEFT JOIN stock_location location_id ON sq.location_id = location_id.id
                          WHERE location_id.usage::text = 'internal'::text
                          GROUP BY (date_trunc('week'::text, to_date(to_char(CURRENT_DATE::timestamp with time zone, 'YYYY/MM/DD'::text), 'YYYY/MM/DD'::text)::timestamp with time zone)), sq.product_id
                        UNION ALL
                         SELECT min(- sm_1.id) AS id,
                            sm_1.product_id,
                                CASE
                                    WHEN sm_1.date_expected > CURRENT_DATE THEN date_trunc('week'::text, to_date(to_char(sm_1.date_expected, 'YYYY/MM/DD'::text), 'YYYY/MM/DD'::text)::timestamp with time zone)
                                    ELSE date_trunc('week'::text, to_date(to_char(CURRENT_DATE::timestamp with time zone, 'YYYY/MM/DD'::text), 'YYYY/MM/DD'::text)::timestamp with time zone)
                                END AS date,
                            sum(sm_1.product_qty) AS product_qty
                           FROM stock_move sm_1
                             LEFT JOIN product_product ON product_product.id = sm_1.product_id
                             LEFT JOIN stock_location dest_location ON sm_1.location_dest_id = dest_location.id
                             LEFT JOIN stock_location source_location ON sm_1.location_id = source_location.id
                          WHERE (sm_1.state::text = ANY (ARRAY['confirmed'::character varying, 'partially_available'::character varying, 'assigned'::character varying, 'waiting'::character varying]::text[])) AND source_location.usage::text <> 'internal'::text AND dest_location.usage::text = 'internal'::text
                          GROUP BY sm_1.date_expected, sm_1.product_id
                        UNION ALL
                         SELECT min(- sm_1.id) AS id,
                            sm_1.product_id,
                                CASE
                                    WHEN sm_1.date_expected > CURRENT_DATE THEN date_trunc('week'::text, to_date(to_char(sm_1.date_expected, 'YYYY/MM/DD'::text), 'YYYY/MM/DD'::text)::timestamp with time zone)
                                    ELSE date_trunc('week'::text, to_date(to_char(CURRENT_DATE::timestamp with time zone, 'YYYY/MM/DD'::text), 'YYYY/MM/DD'::text)::timestamp with time zone)
                                END AS date,
                            sum(- sm_1.product_qty) AS product_qty
                           FROM stock_move sm_1
                             LEFT JOIN product_product ON product_product.id = sm_1.product_id
                             LEFT JOIN stock_location source_location ON sm_1.location_id = source_location.id
                             LEFT JOIN stock_location dest_location ON sm_1.location_dest_id = dest_location.id
                          WHERE (sm_1.state::text = ANY (ARRAY['confirmed'::character varying, 'partially_available'::character varying, 'assigned'::character varying, 'waiting'::character varying]::text[])) AND source_location.usage::text = 'internal'::text AND dest_location.usage::text <> 'internal'::text
                          GROUP BY sm_1.date_expected, sm_1.product_id) main
                     LEFT JOIN ( SELECT DISTINCT date_search.date
                           FROM ( SELECT date_trunc('week'::text, CURRENT_DATE::timestamp with time zone) AS date
                                UNION ALL
                                 SELECT date_trunc('week'::text, to_date(to_char(sm_1.date_expected, 'YYYY/MM/DD'::text), 'YYYY/MM/DD'::text)::timestamp with time zone) AS date
                                   FROM stock_move sm_1
                                     LEFT JOIN stock_location source_location ON sm_1.location_id = source_location.id
                                     LEFT JOIN stock_location dest_location ON sm_1.location_dest_id = dest_location.id
                                  WHERE (sm_1.state::text = ANY (ARRAY['confirmed'::character varying, 'assigned'::character varying, 'waiting'::character varying]::text[])) AND sm_1.date_expected > CURRENT_DATE AND (dest_location.usage::text = 'internal'::text AND source_location.usage::text <> 'internal'::text OR source_location.usage::text = 'internal'::text AND dest_location.usage::text <> 'internal'::text)) date_search) sub ON sub.date IS NOT NULL
                  GROUP BY main.product_id, sub.date, main.date) final
          GROUP BY final.product_id, final.date) sf ON sm.product_id = sf.product_id
  GROUP BY sm.id, sm.product_id
  ORDER BY sm.id, sm.product_id)""")
