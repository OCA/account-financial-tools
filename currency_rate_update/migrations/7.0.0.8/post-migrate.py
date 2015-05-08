# -*- coding: utf-8 -*-
from openerp import pooler, SUPERUSER_ID


state_renames = {
    'currency.rate.update.service': {
        'service': [
            ('CA_BOC_getter', 'BankOfCanadaGetter'),
        ],
    },
}


def rename_states(cr, pool, state_renames):
    """Rename states from an old name to new name

    :param cr: Database Cursor
    :param pool: ORM registry
    :param state_renames: State Renames declaration
    :type state_renames: dict of dict with list of tuple
    """
    for model_name, field_renames in state_renames.iteritems():
        model_pool = pool[model_name]
        for field_name, old_new_values in field_renames.iteritems():
            for old_new_value in old_new_values:
                src, dest = old_new_value
                ids = model_pool.search(cr, SUPERUSER_ID,
                                        [(field_name, '=', src)])
                model_pool.write(cr, SUPERUSER_ID, ids, {field_name: dest})


def migrate(cr, version):
    """Migration entry point

    :param cr: Database Cursor
    :param version: Odoo and module versions
    """
    if version is None:
        return
    pool = pooler.get_pool(cr.dbname)
    rename_states(cr, pool, state_renames)
