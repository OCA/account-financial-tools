# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
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
from openerp.osv.orm import  TransientModel, fields
from openerp.osv.osv import except_osv
from openerp.tools.translate import _
import netsvc
import logging

logger = logging.getLogger('credit.control.line mailing')


class CreditCommunication(TransientModel):
    """Shell calss used to provide a base model to email template and reporting.
       Il use this approche in version 7 a browse record will exist even if not saved"""
    _name = "credit.control.communication"
    _description = "credit control communication"
    _rec_name = 'partner_id'
    _columns = {'partner_id': fields.many2one('res.partner', 'Partner', required=True),

                'current_policy_level': fields.many2one('credit.control.policy.level',
                                                        'Level', required=True),

                'credit_control_line_ids': fields.many2many('credit.control.line',
                                                             rel='comm_credit_rel',
                                                             string='Credit Lines'),

                'company_id': fields.many2one('res.company', 'Company',
                                              required=True),

                'user_id': fields.many2one('res.users', 'User')}

    _defaults = {'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(
                                      cr, uid, 'credit.control.policy', context=c),
                 'user_id': lambda s, cr, uid, c: uid}

    def get_address(self, cursor, uid, com_id, context=None):
        """Return a valid address for customer"""

        context = context  or {}
        if isinstance(com_id, list):
            com_id = com_id[0]
        current = self.browse(cursor, uid, com_id, context=context)
        part_obj = self.pool.get('res.partner')
        adds = part_obj.address_get(cursor, uid, [current.partner_id.id],
                                    adr_pref=['invoice', 'default'])

        add = adds.get('invoice', adds.get('default'))
        if not add:
            raise except_osv(_('No address for partner %s') % (current.partner_id.name),
                             _('Please set one'))
        add_obj = self.pool.get('res.partner.address')
        return add_obj.browse(cursor, uid, add, context=context)


    def get_mail(self, cursor, uid, com_id, context=None):
        """Return a valid email for customer"""
        context = context  or {}
        if isinstance(com_id, list):
            com_id = com_id[0]
        current = self.browse(cursor, uid, com_id, context=context)
        email = current.get_address().email
        if not email:
             raise except_osv(_('No invoicing or default email for partner %s') %
                              (current.partner_id.name),
                              _('Please set one'))
        return email

    def _get_credit_lines(self, cursor, uid, line_ids, partner_id, level_id, context=None):
        """Return credit lines related to a partner and a policy level"""
        cr_line_obj = self.pool.get('credit.control.line')
        cr_l_ids = cr_line_obj.search(cursor,
                                      uid,
                                      [('id', 'in', line_ids),
                                       ('partner_id', '=', partner_id),
                                       ('policy_level_id', '=', level_id)],
                                      context=context)
        #return cr_line_obj.browse(cursor, uid, cr_l_ids, context=context)
        return cr_l_ids

    def _generate_comm_from_credit_line_ids(self, cursor, uid, line_ids, context=None):
        if not line_ids:
            return []
        comms = []
        sql = ("SELECT distinct partner_id, policy_level_id, credit_control_policy_level.level"
               " FROM credit_control_line JOIN credit_control_policy_level "
               "   ON (credit_control_line.policy_level_id = credit_control_policy_level.id)"
               " WHERE credit_control_line.id in %s"
               " ORDER by credit_control_policy_level.level")

        cursor.execute(sql, (tuple(line_ids),))
        res = cursor.dictfetchall()
        for level_assoc in res:
            data = {}
            data['credit_control_line_ids'] = \
                    [(6, 0, self._get_credit_lines(cursor, uid, line_ids,
                                                   level_assoc['partner_id'],
                                                   level_assoc['policy_level_id'],
                                                   context=context))]
            data['partner_id'] = level_assoc['partner_id']
            data['current_policy_level'] = level_assoc['policy_level_id']
            comm_id = self.create(cursor, uid, data, context=context)


            comms.append(self.browse(cursor, uid, comm_id, context=context))
        return comms

    def _generate_mails(self, cursor, uid, comms, context=None):
        """Generate mail message using template related to level"""
        cr_line_obj = self.pool.get('credit.control.line')
        mail_temp_obj = self.pool.get('email.template')
        mail_message_obj = self.pool.get('mail.message')
        mail_ids = []
        for comm in comms:
            # we want to use a local cursor in order to send the maximum
            # of email
            try:
                template = comm.current_policy_level.mail_template_id.id

                # FIXME: usage of this TransientModel is a bit weird with
                # the generation of the email, because the mail is linked
                # with this model, which is transient (only the owner of the
                # record can read it, and it is not persistent)
                # the template should be linked with the credit control line.
                mvalues = mail_temp_obj.generate_email(cursor, uid,
                                                       template,
                                                       comm.id,
                                                       context=context)
                essential_values = ['subject', 'body_html',
                                    'email_from', 'email_to']
                # FIXME: should we really raise an exception?
                # the mail object should handle itself theses cases
                for val in essential_values:
                    if not mvalues.get(val):
                        raise Exception('Mail generation error with %s', val)
                mail_id = mail_message_obj.create(cursor, uid, mvalues, context=context)

                cl_ids = [cl.id for cl in comm.credit_control_line_ids]

                # we do not use local cusros else we have a lock
                # FIXME: so use a savepoint or find the cause of the lock
                # we are not supposed to rollback or commit the main transaction
                cr_line_obj.write(cursor, uid, cl_ids,
                                      {'mail_message_id': mail_id,
                                       'state': 'sent'}, context=context)
                mail_ids.append(mail_id)
            except Exception, exc:
                logger.error(exc)
                cursor.rollback()
                cl_ids = [cl.id for cl in comm.credit_control_line_ids]
                # we do not use local cusros else we have a lock
                cr_line_obj.write(cursor, uid, cl_ids,
                                  {'state': 'mail_error'}, context=context)
            finally:
                cursor.commit()
        return mail_ids

    def _generate_report(self, cursor, uid, comms, context=None):
        """Will generate a report by inserting mako template of related policy template"""
        service = netsvc.LocalService('report.credit_control_summary')
        ids = [x.id for x in comms]
        result, format = service.create(cursor, uid, ids, {}, {})
        return result

    def _mark_credit_line_as_sent(self, cursor, uid, comms, context=None):
        line_ids = []
        for comm in comms:
            line_ids += [x.id for x in comm.credit_control_line_ids]
        l_obj = self.pool.get('credit.control.line')
        l_obj.write(cursor, uid, line_ids, {'state': 'sent'}, context=context)
        return line_ids

