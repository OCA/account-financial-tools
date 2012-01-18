import netsvc
# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Pexego Sistemas Informáticos. All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
"""
Account Importer
"""
__author__ = "Borja López Soilán (Pexego)"

import time
import csv
import base64
import StringIO
import re
from osv import fields,osv
from tools.translate import _

class pxgo_account_importer(osv.osv_memory):
    """
    Account Importer

    Creates accounts from a CSV file.

    The CSV file lines are expected to have at least the code and name of the
    account. 

    The wizard will find the account brothers (or parent) having the same
    account code sufix, and will autocomplete the rest of the account
    parameters (account type, reconcile, parent account...).

    The CSV file lines are tested to be valid account lines using the regular
    expresion options of the wizard.
    """
    _name = "pxgo_account_admin_tools.pxgo_account_importer"
    _description = "Account importation wizard"

    _columns = {
        #
        # Account move parameters
        #
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'overwrite': fields.boolean('Overwrite', help="If the account already exists, overwrite its name?"),
        
        #
        # Input file
        #
        'input_file': fields.binary('File', filters="*.csv", required=True),
        'input_file_name': fields.char('File name', size=256),
        'csv_delimiter': fields.char('Delimiter', size=1, required=True),
        'csv_quotechar': fields.char('Quote', size=1, required=True),
       
        'csv_code_index': fields.integer('Code field', required=True),
        'csv_code_regexp': fields.char('Code regexp', size=32, required=True),
        'csv_name_index': fields.integer('Name field', required=True),
        'csv_name_regexp': fields.char('Name regexp', size=32, required=True),

    }

    _defaults = {
        'company_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid, context).company_id.id,
        'csv_delimiter': lambda *a: ';',
        'csv_quotechar': lambda *a: '"',
        'csv_code_index': lambda *a: 0,
        'csv_name_index': lambda *a: 1,
        'csv_code_regexp': lambda *a: r'^[0-9]+$',
        'csv_name_regexp': lambda *a: r'^.*$',
    }

    def _find_parent_account_id(self, cr, uid, wiz, account_code, context=None):
        """
        Finds the parent account given an account code.
        It will remove the last digit of the code until it finds an account that
        matches exactly the code.
        """
        if len(account_code) > 0:
            parent_account_code = account_code[:-1]
            while len(parent_account_code) > 0:
                account_ids = self.pool.get('account.account').search(cr, uid, [
                                    ('code', '=', parent_account_code),
                                    ('company_id', '=', wiz.company_id.id)
                                ])
                if account_ids and len(account_ids) > 0:
                    return account_ids[0]
                parent_account_code = parent_account_code[:-1]
        # No parent found
        return None

    def _find_brother_account_id(self, cr, uid, wiz, account_code, context=None):
        """
        Finds a brother account given an account code.
        It will remove the last digit of the code until it finds an account that
        matches the begin of the code.
        """
        if len(account_code) > 0:
            brother_account_code = account_code[:-1]
            while len(brother_account_code) > 0:
                account_ids = self.pool.get('account.account').search(cr, uid, [
                                    ('code', '=like', brother_account_code + '%%'),
                                    ('company_id', '=', wiz.company_id.id)
                                ])
                if account_ids and len(account_ids) > 0:
                    return account_ids[0]
                brother_account_code = brother_account_code[:-1]
        # No brother found
        return None

    def action_import(self, cr, uid, ids, context=None):
        """
        Imports the accounts from the CSV file using the options from the
        wizard.
        """
        # List of the imported accounts
        imported_account_ids = []

        for wiz in self.browse(cr, uid, ids, context):
            if not wiz.input_file:
                raise osv.except_osv(_('UserError'), _("You need to select a file!"))


            # Decode the file data
            data = base64.b64decode(wiz.input_file)

            #
            # Read the file
            #
            reader = csv.reader(StringIO.StringIO(data),
                                delimiter=str(wiz.csv_delimiter),
                                quotechar=str(wiz.csv_quotechar))

            for record in reader:
                # Ignore short records
                if len(record) > wiz.csv_code_index \
                        and len(record) > wiz.csv_name_index:

                    record_code = record[wiz.csv_code_index]
                    record_name =  record[wiz.csv_name_index]

                    #
                    # Ignore invalid records
                    #
                    if re.match(wiz.csv_code_regexp, record_code) \
                            and re.match(wiz.csv_name_regexp, record_name):

                        #
                        # Search for the account
                        #
                        account_ids = self.pool.get('account.account').search(cr, uid, [
                                    ('code', '=', record_code),
                                    ('company_id', '=', wiz.company_id.id)
                                ])
                        if account_ids:
                            if wiz.overwrite:
                                netsvc.Logger().notifyChannel('account_importer', netsvc.LOG_DEBUG,
                                    "Overwriting account: %s %s" % (record_code, record_name))
                                self.pool.get('account.account').write(cr, uid, account_ids, {
                                        'name': record_name
                                    })
                                imported_account_ids.extend(account_ids)
                        else:
                            #
                            # Find the account's parent
                            #
                            parent_account_id = self._find_parent_account_id(cr, uid, wiz, record_code)

                            if not parent_account_id:
                                netsvc.Logger().notifyChannel('account_importer', netsvc.LOG_WARNING,
                                        "Couldn't find a parent account for: %s" % record_code)

                            #
                            # Find the account's brother (will be used as template)
                            #
                            brother_account_id = self._find_brother_account_id(cr, uid, wiz, record_code)

                            if not brother_account_id:
                                netsvc.Logger().notifyChannel('account_importer', netsvc.LOG_WARNING,
                                        "Couldn't find a brother account for: %s" % record_code)

                            brother_account = self.pool.get('account.account').browse(cr, uid, brother_account_id)

                            #
                            # Create the new account
                            #
                            netsvc.Logger().notifyChannel('account_importer', netsvc.LOG_DEBUG,
                                "Creating new account: %s %s" % (record_code, record_name))
                            account_id = self.pool.get('account.account').create(cr, uid, {
                                        'code': record_code,
                                        'name': record_name,
                                        'parent_id': parent_account_id,
                                        'type': brother_account.type,
                                        'user_type': brother_account.user_type.id,
                                        'reconcile': brother_account.reconcile,
                                        'company_id': wiz.company_id.id,
                                        'currency_id': brother_account.currency_id.id,
                                        'currency_mode': brother_account.currency_mode,
                                        'active': 1,
                                        'tax_ids': [(6, 0, [tax.id for tax in brother_account.tax_ids])],
                                        'note': False,
                                    })

                            imported_account_ids.append(account_id)
                    else:
                        netsvc.Logger().notifyChannel('account_importer', netsvc.LOG_WARNING,
                                "Invalid record format (ignoring line): %s" % repr(record))
                else:
                    netsvc.Logger().notifyChannel('account_importer', netsvc.LOG_WARNING,
                            "Too short record (ignoring line): %s" % repr(record))

        #
        # Show the accounts to the user
        #
        model_data_ids = self.pool.get('ir.model.data').search(cr, uid, [
                    ('model','=','ir.ui.view'),
                    ('module','=','account'),
                    ('name','=','view_account_form')
                ])
        resource_id = self.pool.get('ir.model.data').read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']

        return {
            'name': _("Imported accounts"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.account',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(False,'tree'), (resource_id,'form')],
            'domain': "[('id', 'in', %s)]" % imported_account_ids,
            'context': context,
        }




pxgo_account_importer()


