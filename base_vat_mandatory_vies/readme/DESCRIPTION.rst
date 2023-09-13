This module extends base_vat module features making the VIES validation mandatory instead of optional
(if VIES option is configured at company level)
It aims to restore the previous behavior of Odoo (before https://github.com/odoo/odoo/commit/eff3b140cc88dd48b77948a577f195f2e1910fd8)

If VIES is unvailable, it fallback on simple vat check.
