# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


def migrate_currency_rate_update(env):
    """ Update field value because service selection field has changed """
    query = """
        UPDATE currency_rate_update_service
        SET {0}=replace({0}, '_getter', '')
        WHERE {0} like '%_getter'
        """
    env.cr.execute(query.format('service'))


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    migrate_currency_rate_update(env)
