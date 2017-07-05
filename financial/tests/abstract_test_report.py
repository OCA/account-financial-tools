# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
#   Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests.common import TransactionCase


class AbstractTestReport(TransactionCase):
    """Common technical tests for all financial reports."""

    def setUp(cls):
        super(AbstractTestReport, cls).setUp()

        cls.model = cls._getReportModel()

        cls.xlsx_report_name = cls._getXlsxReportName()
        cls.xlsx_action_name = cls._getXlsxReportActionName()

        cls.report_title = cls._getReportTitle()

        cls.base_filters = cls._getBaseFilters()
        cls.additional_filters = cls._getAdditionalFiltersToBeTested()

        cls.report = cls.model.create(cls.base_filters)

    def test_01_generation_report_xlsx(self):
        """Check if report XLSX is correctly generated"""

        # Check if returned report action is correct
        report_action = self.report.generate_report()

        self.assertDictContainsSubset(
            {
                'type': 'ir.actions.report.xml',
                'report_name': self.xlsx_report_name,
                'report_type': 'xlsx',
            },
            report_action
        )

        # Check if report template is correct
        report_xlsx = self.env.ref(self.xlsx_action_name).render_report(
            self.report.ids,
            self.xlsx_report_name,
            {'report_type': 'xlsx'}
        )
        self.assertGreaterEqual(len(report_xlsx[0]), 1)
        self.assertEqual(report_xlsx[1], 'xlsx')

    def test_02_compute_data(self):
        """Check that the SQL queries work with all filters options"""

        for filters in [{}] + self.additional_filters:
            current_filter = self.base_filters.copy()
            current_filter.update(filters)
            report = self.model.create(current_filter)
            # TODO: Refatorar este test e o report, pois não podemos garantir
            # que as queries estão sendo executadas da forma correta.
            self.env.ref(self.xlsx_action_name).render_report(
                report.ids,
                self.xlsx_report_name,
                {'report_type': 'xlsx'}
            )

    def _partner_test_is_possible(self, filters):
        """
            :return:
                a boolean to indicate if partner test is possible
                with current filters
        """
        return True

    def _getReportModel(self):
        """
            :return: the report model name
        """
        raise NotImplementedError()

    def _getXlsxReportName(self):
        """
            :return: the xlsx report name
        """
        raise NotImplementedError()

    def _getXlsxReportActionName(self):
        """
            :return: the xlsx report action name
        """
        raise NotImplementedError()

    def _getReportTitle(self):
        """
            :return: the report title displayed into the report
        """
        raise NotImplementedError()

    def _getBaseFilters(self):
        """
            :return: the minimum required filters to generate report
        """
        raise NotImplementedError()

    def _getAdditionalFiltersToBeTested(self):
        """
            :return: the additional filters to generate report variants
        """
        raise NotImplementedError()
