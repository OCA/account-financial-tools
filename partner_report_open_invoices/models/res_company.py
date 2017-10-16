# -*- coding: utf-8 -*-
# Copyright 2016 Serpent Consulting Services Pvt. Ltd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    open_invoices_msg = fields.Text('Open Invoices Message', translate=True,
                                    default='''Dear Sir / Madam,

From our accounting records it appears that some payments on your account
is still open. Please check the details attached. If payment should already
have been paid, please do not consider this.
If not, I pray you stand for the amount indicated below. If there are
any questions or requests about it, please do not hesitate to contact us.
Thank you in advance for your cooperation.
Best Regards,''')
