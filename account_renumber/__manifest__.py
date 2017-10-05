# -*- coding: utf-8 -*-
# Copyright 2009 Pexego Sistemas Informáticos. All Rights Reserved
# Copyright 2013-2017 Pedro Manuel Baeza <pedro.baeza@tecnativa.com>
# Copyright 2013 Joaquin Gutierrez <http://www.gutierrezweb.es>
# Copyright 2016 Jairo Llopis <jairo.llopis@tecnativa.com>
# Copyright 2017 David Vidal <david.vidal@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Account Renumber Wizard",
    'version': "10.0.1.0.1",
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
