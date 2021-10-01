# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tools import sql


def migrate(cr, version):
    sql.rename_column(cr, "res_partner", "auto_archive", "auto_archive_spread")
