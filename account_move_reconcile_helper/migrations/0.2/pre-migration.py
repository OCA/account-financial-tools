# -*- encoding: utf-8 -*-
import logging
from openerp import SUPERUSER_ID
from openerp.modules.registry import RegistryManager
from openerp.addons.account_move_reconcile_helper.post_install\
    import set_reconcile_ref

uid = SUPERUSER_ID

__name__ = 'Set partial mark on reconcile ref'
_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        # it is the installation of the module
        return
    registry = RegistryManager.get(cr.dbname)
    set_reconcile_ref(cr, registry)
