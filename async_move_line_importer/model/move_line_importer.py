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
import csv
import tempfile
from openerp.osv import orm, fields


class move_line_importer(orm.Model):
    """Move line importer"""

    _name = "move.line.importer"
    _inherit = ['mail.thread']
    # _track = {
    #     'state': {
    #         'import.success': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'done',
    #         'import.error': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'error',
    #     },
    # }

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
                                              'Company')
                }

    _defaults = {'delimiter': ','}

    def _get_current_company(self, cr, uid, context=None, model="move.line.importer"):
        return self.pool.get('res.company')._company_default_get(cr, uid, model,
                                                                 context=context)

    _defaults = {'state': 'draft',
                 'name': fields.datetime.now(),
                 'company_id': _get_current_company}

    def _parse_csv(self, cr, uid, imp_id):
        with tempfile.TemporaryFile() as src:
            imp = self.read(cr, uid, imp_id, ['file', 'delimiter'])
            content = imp['file'],
            delimiter = imp['delimiter']
            src.write(content)
            with tempfile.TemporaryFile() as decoded:
                src.seek(0)
                base64.decode(src, decoded)
                decoded.seek(0)
                return self._prepare_csv_data(decoded, delimiter)

    def _prepare_data(self, csv_file, delimiter=","):
        data = csv.reader(csv_file, delimiter=str(delimiter))
        head = data.next()
        # generator does not work in load
        values = [x for x in data]
        return (head, values)

    def import_file(self, cr, uid, imp_id, context=None):
        if isinstance(imp_id, list):
            imp_id = imp_id[0]
        import pdb; pdb.set_trace()
        head, data = self._parse_csv(cr, uid, imp_id)
