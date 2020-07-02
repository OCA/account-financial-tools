from odoo import models, fields


class Journal(models.Model):
    _inherit = 'account.journal'
    assigned_user_ids = fields.Many2many(
        "res.users", string="Assigned users",
        help="Restrict some users to only access their assigned journals. "
             "In order to apply the restriction, the user needs the "
             "'User: Assigned Journals Only' group")
