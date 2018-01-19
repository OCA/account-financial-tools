# Copyright 2012-2017 Camptocamp SA
# Copyright 2017 Okia SPRL (https://okia.be)
# Copyright 2018 Access Bookings Ltd (https://accessbookings.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from odoo import api, fields, models

logger = logging.getLogger(__name__)


class CreditCommunication(models.TransientModel):
    """Shell class used to provide a base model to email template and reporting
    Il use this approche in version 7 a browse record
    will exist even if not saved

    """
    _name = "credit.control.communication"
    _description = "credit control communication"
    _rec_name = 'partner_id'

    partner_id = fields.Many2one('res.partner', 'Partner', required=True)
    current_policy_level = fields.Many2one('credit.control.policy.level',
                                           'Level',
                                           required=True)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True)
    credit_control_line_ids = fields.Many2many('credit.control.line',
                                               rel='comm_credit_rel',
                                               string='Credit Lines')
    contact_address = fields.Many2one('res.partner',
                                      readonly=True)
    report_date = fields.Date(default=fields.Date.context_today)

    @api.model
    def _get_company(self):
        company_obj = self.env['res.company']
        return company_obj._company_default_get('credit.control.policy')

    company_id = fields.Many2one('res.company',
                                 string='Company',
                                 default=lambda self: self._get_company(),
                                 required=True)
    user_id = fields.Many2one('res.users',
                              default=lambda self: self.env.user,
                              string='User')

    total_invoiced = fields.Float(compute='_compute_total')

    total_due = fields.Float(compute='_compute_total')

    @api.model
    def _get_total(self):
        amount_field = 'credit_control_line_ids.amount_due'
        return sum(self.mapped(amount_field))

    @api.model
    def _get_total_due(self):
        balance_field = 'credit_control_line_ids.balance_due'
        return sum(self.mapped(balance_field))

    @api.multi
    @api.depends('credit_control_line_ids',
                 'credit_control_line_ids.amount_due',
                 'credit_control_line_ids.balance_due')
    def _compute_total(self):
        for communication in self:
            communication.total_invoiced = communication._get_total()
            communication.total_due = communication._get_total_due()

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        if vals.get('partner_id'):
            # the computed field does not work in TransientModel,
            # just set a value on creation
            partner_id = vals['partner_id']
            vals['contact_address'] = self._get_contact_address(partner_id).id
        return super(CreditCommunication, self).create(vals)

    @api.multi
    def get_email(self):
        """ Return a valid email for customer """
        self.ensure_one()
        contact = self.contact_address
        return contact.email

    @api.multi
    @api.returns('res.partner')
    def get_contact_address(self):
        """ Compatibility method, please use the contact_address field """
        self.ensure_one()
        return self.contact_address

    @api.model
    @api.returns('res.partner')
    def _get_contact_address(self, partner_id):
        partner_obj = self.env['res.partner']
        partner = partner_obj.browse(partner_id)
        add_ids = partner.address_get(adr_pref=['invoice']) or {}
        add_id = add_ids['invoice']
        return partner_obj.browse(add_id)

    @api.model
    @api.returns('credit.control.line')
    def _get_credit_lines(self, line_ids, partner_id, level_id, currency_id):
        """ Return credit lines related to a partner and a policy level """
        cr_line_obj = self.env['credit.control.line']
        cr_lines = cr_line_obj.search([('id', 'in', line_ids),
                                       ('partner_id', '=', partner_id),
                                       ('policy_level_id', '=', level_id),
                                       ('currency_id', '=', currency_id)])
        return cr_lines

    @api.model
    def _generate_comm_from_credit_lines(self, lines):
        """ Aggregate credit control line by partner, level, and currency
        It also generate a communication object per aggregation.
        """
        comms = self.browse()
        if not lines:
            return comms
        sql = (
            "SELECT distinct partner_id, policy_level_id, "
            " credit_control_line.currency_id, "
            " credit_control_policy_level.level"
            " FROM credit_control_line JOIN credit_control_policy_level "
            "   ON (credit_control_line.policy_level_id = "
            "       credit_control_policy_level.id)"
            " WHERE credit_control_line.id in %s"
            " ORDER by credit_control_policy_level.level, "
            "          credit_control_line.currency_id"
        )
        cr = self.env.cr
        cr.execute(sql, (tuple(lines.ids), ))
        res = cr.dictfetchall()
        company_currency = self.env.user.company_id.currency_id
        for group in res:
            data = {}
            level_lines = self._get_credit_lines(lines.ids,
                                                 group['partner_id'],
                                                 group['policy_level_id'],
                                                 group['currency_id']
                                                 )

            data['credit_control_line_ids'] = [(6, 0, level_lines.ids)]
            data['partner_id'] = group['partner_id']
            data['current_policy_level'] = group['policy_level_id']
            data['currency_id'] = group['currency_id'] or company_currency.id
            comm = self.create(data)
            comms += comm
        return comms

    @api.multi
    @api.returns('mail.mail')
    def _generate_emails(self):
        """ Generate email message using template related to level """
        emails = self.env['mail.mail']
        required_fields = ['subject',
                           'body_html',
                           'email_from',
                           'email_to']
        for comm in self:
            template = comm.current_policy_level.email_template_id
            email_values = template.generate_email(comm.id)
            email_values['message_type'] = 'email'
            # model is Transient record (self) removed periodically so no point
            # of storing res_id
            email_values.pop('model', None)
            email_values.pop('res_id', None)
            email = emails.create(email_values)

            state = 'sent'
            # The mail will not be send, however it will be in the pool, in an
            # error state. So we create it, link it with
            # the credit control line
            # and put this latter in a `email_error` state we not that we have
            # a problem with the email
            if not all(email_values.get(field) for field in required_fields):
                state = 'email_error'

            comm.credit_control_line_ids.write({'mail_message_id': email.id,
                                                'state': state})
            attachments = self.env['ir.attachment']
            for att in email_values.get('attachments', []):
                attach_fname = att[0]
                attach_datas = att[1]
                data_attach = {
                    'name': attach_fname,
                    'datas': attach_datas,
                    'datas_fname': attach_fname,
                    'res_model': 'mail.mail',
                    'res_id': email.id,
                    'type': 'binary',
                }
                attachments |= attachments.create(data_attach)
            email.write({'attachment_ids': [(6, 0, attachments.ids)]})
            emails += email
        return emails

    @api.multi
    @api.returns('credit.control.line')
    def _mark_credit_line_as_sent(self):
        lines = self.env['credit.control.line']
        for comm in self:
            lines |= comm.credit_control_line_ids

        lines.write({'state': 'sent'})
        return lines
