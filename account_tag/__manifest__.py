# -*- coding: utf-8 -*-
{
    'name': "Account Account Tag Enhancement",

    'summary': "Enable Configuration and Enhancement for Account Account Tags",

    'description': """
This module enhances the account.account.tag model by adding a many2many relationship to res.company, 
allowing tags to be associated with multiple companies. It also adds a code field for better identification of tags. 
The module adds configuration views for managing these tags to Invoicing / Configuration / Accounting.
    """,

    #
    # Issuer Specification
    'author': "Michael Blickenstorfer",
    'website': "https://www.blicki.ch",
    'license': "AGPL-3",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Association',
    'version': '18.0.1.0.0',
    'application': False,
    'auto_install': False,
    'installable': True,

    # any module necessary for this one to work correctly
    'depends': [
        'account',
    ],

    # always loaded
    'data': [
        'views/account_account_tag.xml',
    ],

    'assets': {

    },

    'translation_files': [

    ],

    # only loaded in demonstration mode
    'demo': [
        
    ],

    #
    # Hooks
    'pre_init_hook': '_pre_init_hook',
    'post_init_hook': '_post_init_hook',
    'uninstall_hook': '_uninstall_hook',

}

