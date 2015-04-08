from openerp.osv import orm, fields
from openerp import netsvc
import logging


class ResetChart(orm.TransientModel):
    _name = 'account.reset.chart'
    _rec_name = 'company_id'
    _columns = {
        'company_id': fields.many2one(
            'res.company', required=True),
        }

    def reset_chart(self, cr, uid, ids, context=None):
        logger = logging.getLogger('openerp.addons.account_reset_chart')
        wkf_service = netsvc.LocalService('workflow')
        wiz = self.browse(cr, uid, ids[0], context=context)
        company_id = wiz.company_id.id
        move_obj = self.pool['account.move']
        inv_obj = self.pool['account.invoice']
        inv_line_obj = self.pool['account.invoice.line']
        inv_tax_obj = self.pool['account.invoice.tax']

        def unlink_from_company(model):
            logger.info('Unlinking all records of model %s', model)
            obj = self.pool.get(model)
            if not obj:
                logger.info('Model %s not found', model)
                return
            obj_ids = obj.search(
                cr, uid, [('company_id', '=', company_id)],
                context=context)
            obj.unlink(cr, uid, obj_ids)

        payment_obj = self.pool.get('payment.order')
        if payment_obj:
            logger.info('Deleting payment orders.')
            cr.execute(
                """
                DELETE FROM payment_line
                WHERE order_id IN (
                    SELECT id FROM payment_order
                    WHERE company_id = %s);
                """, (company_id,))
            cr.execute(
                "DELETE FROM payment_order WHERE company_id = %s;",
                (company_id,))

            unlink_from_company('payment.mode')

        unlink_from_company('account.banking.account.settings')
        unlink_from_company('res.partner.bank')

        logger.info('Undoing reconciliations')
        rec_obj = self.pool['account.move.reconcile']
        rec_ids = rec_obj.search(
            cr, uid,
            [('line_id.move_id.company_id', '=', company_id)], context=context)
        rec_obj.unlink(cr, uid, rec_ids, context=context)

        logger.info('Reset paid invoices\'s workflows')
        paid_inv_ids = tuple(inv_obj.search(
            cr, uid,
            [('company_id', '=', company_id), ('state', '=', 'paid')],
            context=context))
        if paid_inv_ids:
            cr.execute(
                """
                UPDATE wkf_instance
                SET state = 'active'
                WHERE res_type = 'account_invoice'
                AND res_id IN %s""" % (paid_inv_ids,))
            cr.execute(
                """
                UPDATE wkf_workitem
                SET act_id = (
                    SELECT res_id FROM ir_model_data
                    WHERE module = 'account'
                        AND name = 'act_open')
                WHERE inst_id IN (
                    SELECT id FROM wkf_instance
                    WHERE res_type = 'account_invoice'
                    AND res_id IN %s)
                """ % (paid_inv_ids,))
            for inv_id in paid_inv_ids:
                wkf_service.trg_validate(
                    uid, 'account.invoice', inv_id, 'invoice_cancel', cr)

        logger.info('Dismantling invoices')
        inv_ids = inv_obj.search(
            cr, uid,
            [('company_id', '=', company_id)],
            context=context)
        inv_line_ids = inv_line_obj.search(
            cr, uid, [('invoice_id', 'in', inv_ids)], context=context)
        inv_line_obj.unlink(cr, uid, inv_line_ids, context=context)
        inv_tax_ids = inv_tax_obj.search(
            cr, uid, [('invoice_id', 'in', inv_ids)], context=context)
        inv_tax_obj.unlink(cr, uid, inv_tax_ids, context=context)
        logger.info('Unlinking invoices')
        cr.execute(
            """
            DELETE FROM account_invoice
            WHERE id IN %s""" % (tuple(inv_ids),))

        logger.info('Unlinking moves')
        move_ids = move_obj.search(
            cr, uid, [('company_id', '=', company_id)],
            context=context)
        cr.execute(
            """UPDATE account_move SET state = 'draft'
               WHERE id IN %s""" % (tuple(move_ids),))
        move_obj.unlink(cr, uid, move_ids, context=context)

        unlink_from_company('account.fiscal.position')
        unlink_from_company('account.tax')
        unlink_from_company('account.tax.code')
        unlink_from_company('account.journal')

        logger.info('Unlink properties with account as values')
        cr.execute(
            """
            DELETE FROM ir_property
            WHERE value_reference LIKE 'account.account,%%'
            AND company_id = %s""" % (company_id,))
        unlink_from_company('account.account')
        return True
