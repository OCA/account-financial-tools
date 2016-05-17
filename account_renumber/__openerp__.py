# -*- coding: utf-8 -*-
# © 2009 Pexego Sistemas Informáticos. All Rights Reserved
# © 2013 Pedro Manuel Baeza <pedro.baeza@tecnativa.com>
# © 2013 Joaquin Gutierrez <http://www.gutierrezweb.es>
# © 2016 Jairo Llopis <jairo.llopis@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Account Renumber Wizard",
    'version': "9.0.1.0.0",
    'author': "Pexego,Tecnativa,Odoo Community Association (OCA)",
    'website': "http://www.pexego.es",
    'category': "Accounting & Finance",
    "license": "AGPL-3",
    "depends": [
        'account',
    ],
    "data": [
        'wizard/wizard_renumber_view.xml',
    ],
    'installable': True,
}
