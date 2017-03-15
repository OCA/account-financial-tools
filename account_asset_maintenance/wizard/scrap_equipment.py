# -*- coding: utf-8 -*-
# Copyright 2016 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class WizardPerformEquipmentScrap(models.TransientModel):
    _name = "wizard.perform.equipment.scrap"
    _description = "Perform Scrap (Equipment)"

    scrap_date = fields.Date(required=True)
    equipment_id = fields.Many2one(
        'maintenance.equipment',
        'Equipment',
        required=True
    )

    @api.multi
    def do_scrap(self):
        for wizard in self:
            wizard.equipment_id.scrap_date = wizard.scrap_date
            template = wizard.equipment_id.equipment_scrap_template_id
            if template:
                template.send_mail(wizard.equipment_id.id)
