
try:
    from odoo.addons.report_xlsx_helper.report.abstract_report_xlsx \
        import AbstractReportXlsx
except (ImportError, IOError) as err:
    import logging
    _logger = logging.getLogger(__name__)
    _logger.debug(err)
else:
    from . import account_asset_report_xls
