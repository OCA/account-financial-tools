# Copyright 2012-2017 Camptocamp SA
# Copyright 2017 Okia SPRL (https://okia.be)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    """ Add a settings on the credit control policy to use on the partners,
    and links to the credit control lines.
    """

    _inherit = "res.partner"

    credit_policy_id = fields.Many2one(
        'credit.control.policy',
        string='Credit Control Policy',
        domain="[('account_ids', 'in', property_account_receivable_id)]",
        help="The Credit Control Policy used for this "
             "partner. This setting can be forced on the "
             "invoice. If nothing is defined, it will use "
             "the company setting.",
    )
    credit_control_line_ids = fields.One2many('credit.control.line',
                                              'invoice_id',
                                              string='Credit Control Lines',
                                              readonly=True)
    payment_responsible_id = fields.Many2one(
        comodel_name='res.users',
        ondelete='set null',
        string='Follow-up Responsible',
        help="Optionally you can assign a user to this field, "
             "which will make him responsible for the action.",
        track_visibility="onchange",
    )
    payment_note = fields.Text(
        string='Customer Payment Promise',
        help="Payment Note",
        track_visibility="onchange",
    )
    payment_next_action = fields.Text(
        string='Next Action',
        help="This is the next action to be taken.",
        track_visibility="onchange",
    )
    payment_next_action_date = fields.Date(
        string='Next Action Date',
        help="This is when the manual follow-up is needed.",
    )
    manual_followup = fields.Boolean()

    @api.constrains('credit_policy_id', 'property_account_receivable_id')
    def _check_credit_policy(self):
        """ Ensure that policy on partner are limited to the account policy """
        # sudo needed for those w/o permission that duplicate records
        for partner in self:
            if (not partner.property_account_receivable_id or
                    not partner.sudo().credit_policy_id):
                continue
            account = partner.property_account_receivable_id
            policy = partner.sudo().credit_policy_id
            try:
                policy.check_policy_against_account(account)
            except UserError as err:
                # constrains should raise ValidationError exceptions
                raise ValidationError(err)
