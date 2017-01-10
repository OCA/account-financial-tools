# -*- coding: utf-8 -*-
# © 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# 2 choses à ne pas oublier :
# - ajouter dans __init__.py : from .post_install import update_bank_journals
# - ajouter dans __openerp__.py : 'post_init_hook': 'update_bank_journals',

from openerp import SUPERUSER_ID


def update_chronology_sale_journals(cr, pool):
    ajo = pool['account.journal']
    journal_ids = ajo.search(
        cr, SUPERUSER_ID, [('type', 'in', ('sale', 'sale_refund'))])
    if journal_ids:
        ajo.write(cr, SUPERUSER_ID, journal_ids, {'check_chronology': True})
    return
