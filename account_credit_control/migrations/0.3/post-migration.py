# -*- encoding: utf-8 -*-
import logging
from openerp import SUPERUSER_ID
from openerp.modules.registry import RegistryManager

uid = SUPERUSER_ID

__name__ = 'Change custom_mail_text text field to hmtl field'
_logger = logging.getLogger(__name__)


def migrate_replace_text_with_html(cr, registry):
    cr.execute("""update credit_control_policy_level set
                  custom_mail_text=regexp_replace(custom_mail_text, E'[\\n]',
                                                  '<br/>','g')""")
    cr.execute("""update ir_translation set
                  value=regexp_replace(value, E'[\\n]','<br/>','g')
                  where name='credit.control.policy.level,custom_mail_text'""")


def migrate(cr, version):
    if not version:
        # it is the installation of the module
        return
    registry = RegistryManager.get(cr.dbname)
    migrate_replace_text_with_html(cr, registry)
