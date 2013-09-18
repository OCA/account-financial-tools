# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2013 Camptocamp SA
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
import base64
import threading
import csv
import tempfile

import openerp.pooler as pooler
from openerp.osv import orm, fields
from openerp.tools.translate import _

USE_THREAD = True


class move_line_importer(orm.Model):
    """Move line importer"""

    _name = "move.line.importer"
    _inherit = ['mail.thread']

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default.update(state='draft', report=False)
        return super(move_line_importer, self).copy(cr, uid, id, default=default,
                                                    context=context)

    def track_success(sef, cr, uid, obj, context=None):
        return obj['state'] == 'done'

    def track_error(sef, cr, uid, obj, context=None):
        return obj['state'] == 'error'

    _track = {
        'state': {
            'async_move_line_importer.mvl_imported': track_success,
            'async_move_line_importer.mvl_error': track_error,
        },
    }

    _columns = {'name': fields.datetime('Name',
                                        required=True,
                                        readonly=True),
                'state': fields.selection([('draft', 'New'),
                                           ('running', 'Running'),
                                           ('done', 'Success'),
                                           ('error', 'Error')],
                                          readonly=True,
                                          string='Status'),

                'report': fields.text('Report',
                                      readonly=True),
                'file': fields.binary('File',
                                      required=True),
                'delimiter': fields.selection([(',', ','), (';', ';'), ('|', '|')],
                                              string="CSV delimiter",
                                              required=True),
                'company_id': fields.many2one('res.company',
                                              'Company'),
                'bypass_orm': fields.boolean('Fast import (use with caution)',
                                             help="When enabled import will be faster but"
                                                  " it will not use orm and may"
                                                  " not support all CSV canvas. \n"
                                                  "Entry posted option will be skipped. \n"
                                                  "AA lines will only be crated when"
                                                  " moves are posted. \n"
                                                  "Tax lines computation will be skipped. \n"
                                                  "This option should be used with caution"
                                                  " and in conjonction with provided canvas."),
                }

    _defaults = {'delimiter': ',',
                 'bypass_orm': False}

    def _get_current_company(self, cr, uid, context=None, model="move.line.importer"):
        return self.pool.get('res.company')._company_default_get(cr, uid, model,
                                                                 context=context)

    _defaults = {'state': 'draft',
                 'name': fields.datetime.now(),
                 'company_id': _get_current_company}

    def _parse_csv(self, cr, uid, imp_id):
        """Parse stored CSV file in order to be usable by load method.
        Manage base 64 decoding.
        It will return head (list of first row) and data list of list"""
        with tempfile.TemporaryFile() as src:
            imp = self.read(cr, uid, imp_id, ['file', 'delimiter'])
            content = imp['file']
            delimiter = imp['delimiter']
            src.write(content)
            with tempfile.TemporaryFile() as decoded:
                src.seek(0)
                base64.decode(src, decoded)
                decoded.seek(0)
                return self._prepare_csv_data(decoded, delimiter)

    def _prepare_csv_data(self, csv_file, delimiter=","):
        """Parse and decoded CSV file and return head list
        and data list"""
        data = csv.reader(csv_file, delimiter=str(delimiter))
        head = data.next()
        head = [x.replace(' ', '') for x in head]
        # Generator does not work with orm.BaseModel.load
        values = [tuple(x) for x in data if x]
        return (head, values)

    def format_messages(self, messages):
        res = []
        for msg in messages:
            rows = msg.get('rows', {})
            res.append(_("%s. -- Field: %s -- rows %s to %s") % (msg.get('message', 'N/A'),
                                                                 msg.get('field', 'N/A'),
                                                                 rows.get('from', 'N/A'),
                                                                 rows.get('to', 'N/A')))
        return "\n \n".join(res)

    def _manage_load_results(self, cr, uid, imp_id, result, context=None):
        if not result['messages']:
            msg = _("%s lines imported" % len(result['ids'] or []))
            self.write(cr, uid, [imp_id], {'state': 'done',
                                           'report': msg})
        else:
            cr.rollback()
            msg = self.format_messages(result['messages'])
            self.write(cr, uid, [imp_id], {'state': 'error',
                                           'report': msg})
            cr.commit()
        return imp_id

    def _load_data(self, cr, uid, imp_id, head, data, mode, context=None):
        """Function that does the load management, exception and load report"""
        valid_modes = ('threaded', 'direct')
        if mode not in valid_modes:
            raise ValueError('%s is not in valid mode %s ' % (mode, valid_modes))
        try:
            res = self.pool['account.move'].load(cr, uid, head, data, context=context)
            self._manage_load_results(cr, uid, imp_id, res, context=context)
        except Exception as exc:
            cr.rollback()
            self.write(cr, uid, [imp_id], {'state': 'error'})
            if mode != "threaded":
                raise
            msg = _("Unexpected exception not related to CSV file.\n %s" % repr(exc))
            self.write(cr, uid, [imp_id], {'report': msg})

        finally:
            if mode == 'threaded':
                cr.commit()
                cr.close()
        return imp_id

    def _allows_thread(self, imp_id):
        """Check if there is a async import of this file running"""
        for th in threading.enumerate():
            if th.getName() == 'async_move_line_import_%s' % imp_id:
                raise orm.except_orm(_('An import of this file is already running'),
                                     _('Please try latter'))

    def import_file(self, cr, uid, imp_id, context=None):
        if isinstance(imp_id, list):
            imp_id = imp_id[0]
        if context is None:
            context = {}
        current = self.read(cr, uid, imp_id, ['bypass_orm', 'company_id'],
                            load='_classic_write')
        context['company_id'] = current['company_id']
        bypass_orm = current['bypass_orm']
        if bypass_orm:
            # Tells create funtion to bypass orm
            context['async_bypass_create'] = True
        head, data = self._parse_csv(cr, uid, imp_id)
        self.write(cr, uid, [imp_id], {'state': 'running'})
        if USE_THREAD:
            self._allows_thread(imp_id)
            db_name = cr.dbname
            local_cr = pooler.get_db(db_name).cursor()
            thread = threading.Thread(target=self._load_data,
                                      name='async_move_line_import_%s' % imp_id,
                                      args=(local_cr, uid, imp_id, head, data,
                                            'threaded', context.copy()))
            thread.start()
        else:
            self._load_data(cr, uid, imp_id, head, data, 'direct',
                            context=context)
        return {}
