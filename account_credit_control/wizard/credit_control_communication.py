# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi, Guewen Baconnier
#    Copyright 2012 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import netsvc
import logging
from openerp.osv.orm import TransientModel, fields

logger = logging.getLogger('credit.control.line.mailing')


class CreditCommunication(TransientModel):

    """Shell class used to provide a base model to email template and reporting.
    Il use this approche in version 7 a browse record
    will exist even if not saved

    """
    _name = "credit.control.communication"
    _description = "credit control communication"
    _rec_name = 'partner_id'
    _columns = {
        'partner_id': fields.many2one(
            'res.partner',
            'Partner',
            required=True
        ),

        'current_policy_level': fields.many2one(
            'credit.control.policy.level',
            'Level',
            required=True
        ),

        'credit_control_line_ids': fields.many2many(
            'credit.control.line',
            rel='comm_credit_rel',
            string='Credit Lines'
        ),

        'company_id': fields.many2one(
            'res.company',
            'Company',
            required=True
        ),

        'user_id': fields.many2one('res.users', 'User')
    }

    def _get_comp(self, cr, uid, context=None):
        return self.pool.get('res.company')._company_default_get(
            cr, uid,
            'credit.control.policy',
            context=context
        )

    _defaults = {
        'company_id': _get_comp,
        'user_id': lambda s, cr, uid, c: uid
    }

    def get_email(self, cr, uid, com_id, context=None):
        """Return a valid email for customer"""
        if isinstance(com_id, list):
            assert len(com_id) == 1, "get_email only support one id as param."
            com_id = com_id[0]
        form = self.browse(cr, uid, com_id, context=context)
        contact = form.get_contact_address()
        return contact.email

    def get_contact_address(self, cr, uid, com_id, context=None):
        pmod = self.pool['res.partner']
        if isinstance(com_id, list):
            com_id = com_id[0]
        form = self.browse(cr, uid, com_id, context=context)
        part = form.partner_id
        add_ids = part.address_get(adr_pref=['invoice']) or {}
        add_id = add_ids.get('invoice', add_ids.get('default', False))
        return pmod.browse(cr, uid, add_id, context)

    def _get_credit_lines(self, cr, uid, line_ids, partner_id, level_id,
                          context=None):
        """Return credit lines related to a partner and a policy level"""
        cr_line_obj = self.pool.get('credit.control.line')
        cr_l_ids = cr_line_obj.search(cr,
                                      uid,
                                      [('id', 'in', line_ids),
                                       ('partner_id', '=', partner_id),
                                       ('policy_level_id', '=', level_id)],
                                      context=context)
        return cr_l_ids

    def _generate_comm_from_credit_line_ids(self, cr, uid, line_ids,
                                            context=None):
        """Aggregate credit control line by partner, level, and currency
        It also generate a communication object per aggregation.
        """
        if not line_ids:
            return []
        comms = []
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

        cr.execute(sql, (tuple(line_ids),))
        res = cr.dictfetchall()
        for level_assoc in res:
            data = {}
            data['credit_control_line_ids'] = [
                (
                    6, 0, self._get_credit_lines(
                        cr, uid, line_ids,
                        level_assoc['partner_id'],
                        level_assoc['policy_level_id'],
                        context=context
                    )
                )
            ]
            data['partner_id'] = level_assoc['partner_id']
            data['current_policy_level'] = level_assoc['policy_level_id']
            comm_id = self.create(cr, uid, data, context=context)
            comms.append(self.browse(cr, uid, comm_id, context=context))
        return comms

    def _generate_emails(self, cr, uid, comms, context=None):
        """Generate email message using template related to level"""
        cr_line_obj = self.pool.get('credit.control.line')
        email_temp_obj = self.pool.get('email.template')
        email_message_obj = self.pool.get('mail.mail')
        att_obj = self.pool.get('ir.attachment')
        email_ids = []
        essential_fields = ['subject',
                            'body_html',
                            'email_from',
                            'email_to']

        for comm in comms:
            # we want to use a local cr in order to send the maximum
            # of email
            template = comm.current_policy_level.email_template_id.id
            email_values = {}
            cl_ids = [cl.id for cl in comm.credit_control_line_ids]
            email_values = email_temp_obj.generate_email(cr, uid,
                                                         template,
                                                         comm.id,
                                                         context=context)
            email_values['body_html'] = email_values['body']
            email_values['type'] = 'email'

            email_id = email_message_obj.create(cr, uid, email_values,
                                                context=context)

            state = 'sent'
            # The mail will not be send, however it will be in the pool, in an
            # error state. So we create it, link it with
            # the credit control line
            # and put this latter in a `email_error` state we not that we have
            # a problem with the email
            if any(not email_values.get(field) for field in essential_fields):
                state = 'email_error'

            cr_line_obj.write(
                cr, uid, cl_ids,
                {'mail_message_id': email_id,
                 'state': state},
                context=context
            )
            att_ids = []
            for att in email_values.get('attachments', []):
                attach_fname = att[0]
                attach_datas = att[1]
                data_attach = {
                    'name': attach_fname,
                    'datas': attach_datas,
                    'datas_fname': attach_fname,
                    'res_model': 'mail.mail',
                    'res_id': email_id,
                    'type': 'binary',
                }
                att_ids.append(
                    att_obj.create(cr, uid, data_attach,
                                   context=context)
                )
            email_message_obj.write(cr, uid, [email_id],
                                    {'attachment_ids': [(6, 0, att_ids)]},
                                    context=context)
            email_ids.append(email_id)
        return email_ids

    def _generate_report(self, cr, uid, comms, context=None):
        """Will generate a report by inserting mako template
        of related policy template

        """
        service = netsvc.LocalService('report.credit_control_summary')
        ids = [x.id for x in comms]
        result, format = service.create(cr, uid, ids, {}, {})
        return result

    def _mark_credit_line_as_sent(self, cr, uid, comms, context=None):
        line_ids = []
        for comm in comms:
            line_ids += [x.id for x in comm.credit_control_line_ids]
        l_obj = self.pool.get('credit.control.line')
        l_obj.write(cr, uid, line_ids, {'state': 'sent'}, context=context)
        return line_ids
