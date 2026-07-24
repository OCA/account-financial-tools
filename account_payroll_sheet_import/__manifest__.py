{
    "name": "Payroll Sheet Importer",
    "summary": "Import payroll from sheet files and generate journal entries",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "author": "APSL-Nagarro, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "license": "AGPL-3",
    "maintainers": ["BernatObrador"],
    "depends": ["account", "hr"],
    "external_dependencies": {
        "python": [
            "pandas",
            "openpyxl>=3.1.0",
        ]
    },
    "data": [
        "security/payroll_import_security.xml",
        "security/ir.model.access.csv",
        "views/payroll_import_mapping.xml",
        "wizard/payroll_import_wizard.xml",
        "wizard/missing_partner_wizard.xml",
    ],
}
