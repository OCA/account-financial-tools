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
import sys
import traceback
import logging
import base64
import threading
import csv
import tempfile

import psycopg2

import openerp.pooler as pooler
from openerp.osv import orm, fields
from openerp.tools.translate import _


_logger = logging.getLogger(__name__)


class move_line_importer(orm.Model):
    """Asynchrone move / move line importer.

    It will parse the saved CSV file using orm.BaseModel.load
    in a thread. If you set bypass_orm to True then the load function
    will use a totally overridden create function that is a lot faster
    but that totally bypass the ORM

    """

    _name = "move.line.importer"
    _inherit = ['mail.thread']

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default.update(state='draft', report=False)
        return super(move_line_importer, self).copy(cr, uid, id,
                                                    default=default,
                                                    context=context)

    def track_success(sef, cr, uid, obj, context=None):
        """Used by mail subtype"""
        return obj['state'] == 'done'

    def track_error(sef, cr, uid, obj, context=None):
        """Used by mail subtype"""
        return obj['state'] == 'error'

    _track = {
        'state': {
            'async_move_line_importer.mvl_imported': track_success,
            'async_move_line_importer.mvl_error': track_error,
        },
    }

    _columns = {
        'name': fields.datetime(
            'Name',
            required=True,
            readonly=True
        ),
        'state': fields.selection(
            [('draft', 'New'),
             ('running', 'Running'),
             ('done', 'Success'),
             ('error', 'Error')],
            readonly=True,
            string='Status'
        ),
        'report': fields.text(
            'Report',
            readonly=True
        ),
        'file': fields.binary(
            'File',
            required=True
        ),
        'delimiter': fields.selection(
            [(',', ','), (';', ';'), ('|', '|')],
            string="CSV delimiter",
            required=True
        ),
        'company_id': fields.many2one(
            'res.company',
            'Company'
        ),
        'bypass_orm': fields.boolean(
            'Fast import (use with caution)',
            help="When enabled import will be faster but"
                 " it will not use orm and may"
                 " not support all CSV canvas. \n"
                 "Entry posted option will be skipped. \n"
                 "AA lines will only be created when"
                 " moves are posted. \n"
                 "Tax lines computation will be skipped. \n"
                 "This option should be used with caution"
                 " and in conjonction with provided canvas."
        ),
    }

    def _get_current_company(self, cr, uid, context=None,
                             model="move.line.importer"):
        return self.pool.get('res.company')._company_default_get(
            cr, uid,
            model,
            context=context
        )

    _defaults = {'state': 'draft',
                 'name': fields.datetime.now(),
                 'company_id': _get_current_company,
                 'delimiter': ',',
                 'bypass_orm': False}

    def _parse_csv(self, cr, uid, imp_id):
        """Parse stored CSV file in order to be usable by BaseModel.load method.

        Manage base 64 decoding.

        :param imp_id: current importer id
        :returns: (head [list of first row], data [list of list])

        """
        # We use tempfile in order to avoid memory error with large files
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
        """Parse a decoded CSV file and return head list and data list

        :param csv_file: decoded CSV file
        :param delimiter: CSV file delimiter char
        :returns: (head [list of first row], data [list of list])

        """
        try:
            data = csv.reader(csv_file, delimiter=str(delimiter))
        except csv.Error as error:
            raise orm.except_orm(
                _('CSV file is malformed'),
                _("Maybe you have not choose correct separator \n"
                  "the error detail is : \n %s") % repr(error)
            )
        head = data.next()
        head = [x.replace(' ', '') for x in head]
        # Generator does not work with orm.BaseModel.load
        values = [tuple(x) for x in data if x]
        return (head, values)

    def format_messages(self, messages):
        """Format error messages generated by the BaseModel.load method

        :param messages: return of BaseModel.load messages key
        :returns: formatted string

        """
        res = []
        for msg in messages:
            rows = msg.get('rows', {})
            res.append(_("%s. -- Field: %s -- rows %s to %s") % (
                msg.get('message', 'N/A'),
                msg.get('field', 'N/A'),
                rows.get('from', 'N/A'),
                rows.get('to', 'N/A'))
            )
        return "\n \n".join(res)

    def _manage_load_results(self, cr, uid, imp_id, result, _do_commit=True,
                             context=None):
        """Manage the BaseModel.load function output and store exception.

        Will generate success/failure report and store it into report field.
        Manage commit and rollback even if load method uses PostgreSQL
        Savepoints.

        :param imp_id: current importer id
        :param result: BaseModel.load returns
                       {ids: list(int)|False, messages: [Message]}
        :param _do_commit: toggle commit management only used
                           for testing purpose only
        :returns: current importer id

        """
        # Import sucessful
        state = msg = None
        if not result['messages']:
            msg = _("%s lines imported" % len(result['ids'] or []))
            state = 'done'
        else:
            if _do_commit:
                cr.rollback()
            msg = self.format_messages(result['messages'])
            state = 'error'
        return (imp_id, state, msg)

    def _write_report(self, cr, uid, imp_id, state, msg, _do_commit=True,
                      max_tries=5, context=None):
        """Commit report in a separated transaction.

        It will  avoid concurrent update error due to mail.message.
        If transaction trouble happen we try 5 times to rewrite report

        :param imp_id: current importer id
        :param state: import state
        :param msg: report summary
        :returns: current importer id

        """
        if _do_commit:
            db_name = cr.dbname
            local_cr = pooler.get_db(db_name).cursor()
            try:
                self.write(local_cr, uid, [imp_id],
                           {'state': state, 'report': msg},
                           context=context)
                local_cr.commit()
            # We handle concurrent error troubles
            except psycopg2.OperationalError as pg_exc:
                _logger.error(
                    "Can not write report. "
                    "System will retry %s time(s)" % max_tries
                )
                if (pg_exc.pg_code in orm.PG_CONCURRENCY_ERRORS_TO_RETRY and
                        max_tries >= 0):
                    local_cr.rollback()
                    local_cr.close()
                    remaining_try = max_tries - 1
                    self._write_report(cr, uid, imp_id, cr,
                                       _do_commit=_do_commit,
                                       max_tries=remaining_try,
                                       context=context)
                else:
                    _logger.exception(
                        'Can not log report - Operational update error'
                    )
                    raise
            except Exception:
                _logger.exception('Can not log report')
                local_cr.rollback()
                raise
            finally:
                if not local_cr.closed:
                    local_cr.close()
        else:
            self.write(cr, uid, [imp_id],
                       {'state': state, 'report': msg},
                       context=context)
        return imp_id

    def _load_data(self, cr, uid, imp_id, head, data, _do_commit=True,
                   context=None):
        """Function that does the load of parsed CSV file.

        If will log exception and susccess into the report fields.

        :param imp_id: current importer id
        :param head: CSV file head (list of header)
        :param data: CSV file content (list of data list)
        :param _do_commit: toggle commit management
                           only used for testing purpose only
        :returns: current importer id

        """
        state = msg = None
        try:
            res = self.pool['account.move'].load(cr, uid, head, data,
                                                 context=context)
            r_id, state, msg = self._manage_load_results(cr, uid, imp_id, res,
                                                         _do_commit=_do_commit,
                                                         context=context)
        except Exception as exc:
            if _do_commit:
                cr.rollback()
            ex_type, sys_exc, tb = sys.exc_info()
            tb_msg = ''.join(traceback.format_tb(tb, 30))
            _logger.error(tb_msg)
            _logger.error(repr(exc))
            msg = _("Unexpected exception.\n %s \n %s" % (repr(exc), tb_msg))
            state = 'error'
        finally:
            self._write_report(cr, uid, imp_id, state, msg,
                               _do_commit=_do_commit, context=context)
            if _do_commit:
                try:
                    cr.commit()
                except psycopg2.Error:
                    _logger.exception('Can not do final commit')
                cr.close()
        return imp_id

    def _allows_thread(self, imp_id):
        """Check if there is a async import of this file running

        :param imp_id: current importer id
        :returns: void
        :raise: orm.except in case on failure

        """
        for th in threading.enumerate():
            if th.getName() == 'async_move_line_import_%s' % imp_id:
                raise orm.except_orm(
                    _('An import of this file is already running'),
                    _('Please try latter')
                )

    def _check_permissions(self, cr, uid, context=None):
        """Ensure that user is allowed to create move / move line"""
        move_obj = self.pool['account.move']
        move_line_obj = self.pool['account.move.line']
        move_obj.check_access_rule(cr, uid, [], 'create')
        move_obj.check_access_rights(cr, uid, 'create', raise_exception=True)
        move_line_obj.check_access_rule(cr, uid, [], 'create')
        move_line_obj.check_access_rights(cr, uid, 'create',
                                          raise_exception=True)

    def import_file(self, cr, uid, imp_id, context=None):
        """ Will do an asynchronous load of a CSV file.

        Will generate an success/failure report and generate some
        maile threads. It uses BaseModel.load to lookup CSV.
        If you set bypass_orm to True then the load function
        will use a totally overridden create function that is a lot faster
        but that totally bypass the ORM

        """

        if isinstance(imp_id, list):
            imp_id = imp_id[0]
        if context is None:
            context = {}
        context = context.copy()
        current = self.read(cr, uid, imp_id, ['bypass_orm', 'company_id'],
                            load='_classic_write')
        context['company_id'] = current['company_id']
        bypass_orm = current['bypass_orm']
        if bypass_orm:
            # Tells create funtion to bypass orm
            # As we bypass orm we ensure that
            # user is allowed to creat move / move line
            self._check_permissions(cr, uid, context=context)
            context['async_bypass_create'] = True
        head, data = self._parse_csv(cr, uid, imp_id)
        self.write(cr, uid, [imp_id], {'state': 'running',
                                       'report': _('Import is running')})
        self._allows_thread(imp_id)
        db_name = cr.dbname
        local_cr = pooler.get_db(db_name).cursor()
        thread = threading.Thread(target=self._load_data,
                                  name='async_move_line_import_%s' % imp_id,
                                  args=(local_cr, uid, imp_id, head, data),
                                  kwargs={'context': context.copy()})
        thread.start()

        return {}
