# Copyright 2019 Apps2GROW - Henrik Norlin
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade
import logging
logger = logging.getLogger('OpenUpgrade')


def create_view_asset(env):
    for company in env['res.company'].search([]):
        values = {
            'company_id': company.id,
            'name': 'ASSET VIEW',
            'type': 'view',
        }
        env['account.asset'].create(values)


def update_asset(cr):
    cr.execute('''SELECT a.id,
                         a.openupgrade_legacy_12_0_method_number,
                         a.openupgrade_legacy_12_0_method_period,
                         p.account_analytic_id,
                         a.company_id
                    FROM account_asset a
                    LEFT JOIN account_asset_profile p ON a.profile_id = p.id
                   WHERE a.type = 'normal';''')
    for asset in cr.fetchall():
        no_of_entries = asset[1]
        months_between_entries = asset[2]

        values = {}
        # Analytic account
        values['account_analytic_id'] = asset[3] or 'NULL'
        # Number of years
        values['method_number'] = \
            int(no_of_entries * months_between_entries / 12)
        # Period: month / quarter / year (default: year)
        if months_between_entries == 3:
            values['method_period'] = "'quarter'"
        elif months_between_entries == 1:
            values['method_period'] = "'month'"
        cr.execute("""SELECT id FROM account_asset
            WHERE type = 'view' and company_id = %s limit 1;""" % asset[4])
        values['parent_id'] = cr.fetchall()[0][0]

        vals = ['%s = %s' % (key, value) for key, value in values.items()]
        sql = "UPDATE account_asset SET %s WHERE id = %s" % \
              (', '.join(vals), asset[0])
        logger.debug('update_asset: %s' % sql)
        cr.execute(sql)


def update_asset_profile(cr):
    cr.execute('''SELECT id,
                         openupgrade_legacy_12_0_method_number,
                         openupgrade_legacy_12_0_method_period,
                         company_id FROM account_asset_profile;''')
    for profile in cr.fetchall():

        no_of_entries = profile[1]
        months_between_entries = profile[2]

        values = {}
        # Number of years
        values['method_number'] = \
            int(no_of_entries * months_between_entries / 12)
        # Period: month / quarter / year (default: year)
        if months_between_entries == 3:
            values['method_period'] = "'quarter'"
        elif months_between_entries == 1:
            values['method_period'] = "'month'"
        cr.execute("""SELECT id FROM account_asset
            WHERE type = 'view' and company_id = %s
            LIMIT 1;""" % profile[3])
        values['parent_id'] = cr.fetchall()[0][0]

        vals = ['{} = {}'.format(key, value) for key, value in values.items()]
        sql = """UPDATE account_asset_profile
                 SET %s WHERE id = %s""" % (', '.join(vals), profile[0])
        logger.debug('update_asset_profile: %s' % sql)
        cr.execute(sql)


def update_move_line(cr):
    cr.execute("""SELECT l.move_id, l.asset_id, a.profile_id
        FROM account_asset_line l
        LEFT JOIN account_asset a ON l.asset_id = a.id
        WHERE l.move_id IS NOT NULL;""")
    for line in cr.fetchall():
        sql = """UPDATE account_move_line
                 SET asset_id = %s, asset_profile_id = %s
                 WHERE move_id = %s""" % (line[1], line[2], line[0])
        logger.debug('update_move_line: %s' % sql)
        cr.execute(sql)


@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    create_view_asset(env)
    update_asset(cr)
    update_asset_profile(cr)
    update_move_line(cr)
