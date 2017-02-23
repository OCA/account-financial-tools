# -*- coding: utf-8 -*-
# Copyright 2004-2010 Tiny SPRL (<http://tiny.be>)
# Copyright 2007 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
from openerp.exceptions import ValidationError


class AccountFollowup(models.Model):
    _name = 'account_followup.followup'
    _description = 'Account Follow-up'
    _rec_name = 'name'

    followup_line = fields.One2many(
        comodel_name='account_followup.followup.line',
        inverse_name='followup_id',
        string='Follow-up',
        copy=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id,
    )
    name = fields.Char(
        string="Name",
        related="company_id.name",
    )

    @api.multi
    @api.constrains('company_id')
    def _check_journal_id(self):
        if len(self.company_id) > 1:
            raise ValidationError(
                _('Only one follow-up per company is allowed.'))


class AccountFollowupLine(models.Model):
    _name = 'account_followup.followup.line'
    _description = 'Follow-up Criteria'

    name = fields.Char(
        string='Follow-Up Action',
        required=True,
    )
    sequence = fields.Integer(
        string='Sequence',
        help="Gives the sequence order when displaying a list of follow-up "
             "lines.",
    )
    delay = fields.Integer(
        string='Due Days',
        required=True,
        help="The number of days after the due date of the invoice to wait "
             "before sending the reminder.  Could be negative if you want to "
             "send a polite alert beforehand.",
    )
    followup_id = fields.Many2one(
        comodel_name='account_followup.followup',
        string='Follow Ups',
        required=True,
        ondelete="cascade",
    )
    description = fields.Text(
        string='Printed Message',
        translate=True,
        default='_get_default_description',
    )
    send_email = fields.Boolean(
        string='Send an Email',
        help="When processing, it will send an email",
        default=True,
    )
    send_letter = fields.Boolean(
        string='Send a Letter',
        help="When processing, it will print a letter",
        default=True,
    )
    manual_action = fields.Boolean(
        string='Manual Action',
        help="When processing, it will set the manual action to be taken "
             "for that customer.",
    )
    manual_action_note = fields.Text(
        string='Action To Do',
        placeholder="e.g. Give a phone call, check with others, ...",
    )
    manual_action_responsible_id = fields.Many2one(
        comodel_name='res.users',
        string='Assign a Responsible',
        ondelete='set null',
    )
    email_template_id = fields.Many2one(
        comodel_name='mail.template',
        string='Email Template',
        ondelete='set null',
        default='_get_default_template',
    )
    _order = 'delay'
    _sql_constraints = [
        ('days_uniq',
         'unique(followup_id, delay)',
         'Days of the follow-up levels must be different')]

    @api.model
    def _get_default_description(self):
        return """
            Dear %(partner_name)s,

            Exception made if there was a mistake of ours, it seems that the
            following amount stays unpaid. Please, take appropriate measures
            in order to carry out this payment in the next 8 days.

            Would your payment have been carried out after this mail was sent,
            please ignore this message. Do not hesitate to contact our
            accounting department.

            Best Regards,
        """

    @api.model
    def _get_default_template(self):
        try:
            return self.env.ref(
                'account_followup.email_template_account_followup_default')[1]
        except ValueError:
            return False

    @api.multi
    @api.constrains('description')
    def _check_description(self):
        for line in self.with_context(lang=self.env.user.lang):
            if line.description:
                try:
                    line.description % {
                        'partner_name': '',
                        'date': '',
                        'user_signature': '',
                        'company_name': ''
                    }
                except:
                    raise ValidationError(
                        _('Your description is invalid, use the right legend '
                          'or %% if you want to use the percent character.')
                    )
        return True
