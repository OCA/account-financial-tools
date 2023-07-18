import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        "external_dependencies_override": {
            "python": {"setuptools": "setuptools<58.0.0"}
        }
    },
)
