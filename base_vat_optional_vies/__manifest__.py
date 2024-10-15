# Copyright 2015 Tecnativa - Antonio Espinosa
# Copyright 2016 Tecnativa - Sergio Teruel
# Copyright 2017 Tecnativa - David Vidal
# Copyright 2019 FactorLibre - Rodrigo Bonilla
# Copyright 2022 Moduon - Eduardo de Miguel
# Copyright 2023 Moduon - Emilio Pascual
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Optional validation of VAT via VIES",
    "category": "Accounting",
    "version": "14.0.2.1.0",
    "depends": ["base_vat"],
    "external_dependencies": {"python": ["zeep"]},
    "data": [
        "views/res_partner_view.xml",
        "views/res_config_settings_views.xml",
    ],
    "author": "Tecnativa," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "license": "AGPL-3",
    "installable": True,
}
