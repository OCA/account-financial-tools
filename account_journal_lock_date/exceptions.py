# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError


class JournalLockDateError(UserError):
    pass


class JournalPermanentLockDateError(UserError):
    pass


class AccesRightsLockError(UserError):
    pass
