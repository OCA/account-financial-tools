# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models


class BaseLanguageInstall(models.TransientModel):
    _inherit = "base.language.install"

    def lang_install(self):
        """Reload this addon's translations after a language install.

        account_usability shares translation terms (e.g. ``menu_finance``)
        with core addons like ``account``. The standard install may pick
        another addon's translation for such a term, so we re-run
        ``_update_translations`` scoped to this module to make sure its own
        ``.po`` wins for the newly installed languages.
        """
        res = super().lang_install()
        self.ensure_one()
        module = self.env.ref("base.module_account_usability")
        module._update_translations(self.lang_ids.mapped("code"), self.overwrite)
        return res
