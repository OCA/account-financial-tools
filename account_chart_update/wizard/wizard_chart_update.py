# Copyright 2010 Jordi Esteve, Zikzakmedia S.L. (http://www.zikzakmedia.com)
# Copyright 2010 Pexego Sistemas Informáticos S.L.(http://www.pexego.es)
#        Borja López Soilán
# Copyright 2013 Joaquin Gutierrez (http://www.gutierrezweb.es)
# Copyright 2015 Antonio Espinosa <antonioea@tecnativa.com>
# Copyright 2016 Jairo Llopis <jairo.llopis@tecnativa.com>
# Copyright 2016 Jacques-Etienne Baudoux <je@bcim.be>
# Copyright 2018 Tecnativa - Pedro M. Baeza
# Copyright 2020 Noviat - Luc De Meyer
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from contextlib import closing
from io import StringIO

from odoo import _, api, exceptions, fields, models, tools
from odoo.tools import config

_logger = logging.getLogger(__name__)
EXCEPTION_TEXT = "Traceback (most recent call last)"


class WizardUpdateChartsAccounts(models.TransientModel):
    _name = "wizard.update.charts.accounts"
    _description = "Wizard Update Charts Accounts"

    state = fields.Selection(
        selection=[
            ("init", "Configuration"),
            ("ready", "Select records to update"),
            ("done", "Wizard completed"),
        ],
        string="Status",
        readonly=True,
        default="init",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.user.company_id.id,
    )
    chart_template_id = fields.Many2one(
        comodel_name="account.chart.template",
        string="Chart Template",
        ondelete="cascade",
        required=True,
    )
    chart_template_ids = fields.Many2many(
        "account.chart.template",
        string="Chart Templates",
        compute="_compute_chart_template_ids",
        help="Includes all chart templates.",
    )
    code_digits = fields.Integer(related="chart_template_id.code_digits")
    lang = fields.Selection(
        lambda self: self._get_lang_selection_options(),
        "Language",
        required=True,
        help="For records searched by name (taxes, fiscal "
        "positions), the template name will be matched against the "
        "record name on this language.",
        default=lambda self: self.env.context.get("lang", self.env.user.lang),
    )
    update_tax = fields.Boolean(
        string="Update taxes",
        default=True,
        help="Existing taxes are updated. Taxes are searched by name.",
    )
    update_tax_repartition_line_account = fields.Boolean(
        string="Update Tax Accounts",
        default=True,
        help="Update account_id field on existing Tax repartition lines",
    )
    update_tax_repartition_line_tags = fields.Boolean(
        string="Update Tax Tags",
        default=True,
        help="Update tag_ids field on existing Tax repartition lines",
    )
    update_account = fields.Boolean(
        string="Update accounts",
        default=True,
        help="Existing accounts are updated. Accounts are searched by code.",
    )
    update_fiscal_position = fields.Boolean(
        string="Update fiscal positions",
        default=True,
        help="Existing fiscal positions are updated. Fiscal positions are "
        "searched by name.",
    )
    continue_on_errors = fields.Boolean(
        string="Continue on errors",
        default=False,
        help="If set, the wizard will continue to the next step even if "
        "there are minor errors.",
    )
    recreate_xml_ids = fields.Boolean(string="Recreate missing XML-IDs")
    tax_ids = fields.One2many(
        comodel_name="wizard.update.charts.accounts.tax",
        inverse_name="update_chart_wizard_id",
        string="Taxes",
    )
    account_ids = fields.One2many(
        comodel_name="wizard.update.charts.accounts.account",
        inverse_name="update_chart_wizard_id",
        string="Accounts",
    )
    fiscal_position_ids = fields.One2many(
        comodel_name="wizard.update.charts.accounts.fiscal.position",
        inverse_name="update_chart_wizard_id",
        string="Fiscal positions",
    )
    new_taxes = fields.Integer(string="New taxes", compute="_compute_new_taxes_count")
    new_accounts = fields.Integer(
        string="New accounts", compute="_compute_new_accounts_count"
    )
    rejected_new_account_number = fields.Integer()
    new_fps = fields.Integer(
        string="New fiscal positions", compute="_compute_new_fps_count"
    )
    updated_taxes = fields.Integer(
        string="Updated taxes", compute="_compute_updated_taxes_count"
    )
    rejected_updated_account_number = fields.Integer()
    updated_accounts = fields.Integer(
        string="Updated accounts", compute="_compute_updated_accounts_count"
    )
    updated_fps = fields.Integer(
        string="Updated fiscal positions", compute="_compute_updated_fps_count"
    )
    deleted_taxes = fields.Integer(
        string="Deactivated taxes", compute="_compute_deleted_taxes_count"
    )
    log = fields.Text(string="Messages and Errors", readonly=True)
    tax_field_ids = fields.Many2many(
        comodel_name="ir.model.fields",
        relation="wizard_update_charts_tax_fields_rel",
        string="Tax fields",
        domain=lambda self: self._domain_tax_field_ids(),
        default=lambda self: self._default_tax_field_ids(),
    )
    account_field_ids = fields.Many2many(
        comodel_name="ir.model.fields",
        relation="wizard_update_charts_account_fields_rel",
        string="Account fields",
        domain=lambda self: self._domain_account_field_ids(),
        default=lambda self: self._default_account_field_ids(),
    )
    fp_field_ids = fields.Many2many(
        comodel_name="ir.model.fields",
        relation="wizard_update_charts_fp_fields_rel",
        string="Fiscal position fields",
        domain=lambda self: self._domain_fp_field_ids(),
        default=lambda self: self._default_fp_field_ids(),
    )
    tax_matching_ids = fields.One2many(
        comodel_name="wizard.tax.matching",
        inverse_name="update_chart_wizard_id",
        string="Taxes matching",
        default=lambda self: self._default_tax_matching_ids(),
    )
    account_matching_ids = fields.One2many(
        comodel_name="wizard.account.matching",
        inverse_name="update_chart_wizard_id",
        string="Accounts matching",
        default=lambda self: self._default_account_matching_ids(),
    )
    fp_matching_ids = fields.One2many(
        comodel_name="wizard.fp.matching",
        inverse_name="update_chart_wizard_id",
        string="Fiscal positions matching",
        default=lambda self: self._default_fp_matching_ids(),
    )

    def _domain_per_name(self, name):
        return [
            ("model", "=", name),
            ("name", "not in", tuple(self.fields_to_ignore(name))),
        ]

    def _domain_tax_field_ids(self):
        return self._domain_per_name("account.tax.template")

    def _domain_account_field_ids(self):
        return self._domain_per_name("account.account.template")

    def _domain_fp_field_ids(self):
        return self._domain_per_name("account.fiscal.position.template")

    def _default_tax_field_ids(self):
        return [
            (4, x.id)
            for x in self.env["ir.model.fields"].search(self._domain_tax_field_ids())
        ]

    def _default_account_field_ids(self):
        return [
            (4, x.id)
            for x in self.env["ir.model.fields"].search(
                self._domain_account_field_ids()
            )
        ]

    def _default_fp_field_ids(self):
        return [
            (4, x.id)
            for x in self.env["ir.model.fields"].search(self._domain_fp_field_ids())
        ]

    def _get_matching_ids(self, model_name, ordered_opts):
        vals = []
        for seq, opt in enumerate(ordered_opts, 1):
            vals.append((0, False, {"sequence": seq, "matching_value": opt}))

        all_options = self.env[model_name]._get_matching_selection()
        all_options = map(lambda x: x[0], all_options)
        all_options = list(set(all_options) - set(ordered_opts))

        for seq, opt in enumerate(all_options, len(ordered_opts) + 1):
            vals.append((0, False, {"sequence": seq, "matching_value": opt}))

        return vals

    def _default_fp_matching_ids(self):
        ordered_opts = ["xml_id", "name"]
        return self._get_matching_ids("wizard.fp.matching", ordered_opts)

    def _default_tax_matching_ids(self):
        ordered_opts = ["xml_id", "description", "name"]
        return self._get_matching_ids("wizard.tax.matching", ordered_opts)

    def _default_account_matching_ids(self):
        ordered_opts = ["xml_id", "code", "name"]
        return self._get_matching_ids("wizard.account.matching", ordered_opts)

    @api.model
    def _get_lang_selection_options(self):
        """Gets the available languages for the selection."""
        langs = self.env["res.lang"].search([])
        return [(lang.code, lang.name) for lang in langs]

    @api.depends("chart_template_id")
    def _compute_chart_template_ids(self):
        all_parents = self.chart_template_id._get_chart_parent_ids()
        self.chart_template_ids = all_parents

    @api.depends("tax_ids")
    def _compute_new_taxes_count(self):
        self.new_taxes = len(self.tax_ids.filtered(lambda x: x.type == "new"))

    @api.depends("account_ids")
    def _compute_new_accounts_count(self):
        self.new_accounts = (
            len(self.account_ids.filtered(lambda x: x.type == "new"))
            - self.rejected_new_account_number
        )

    @api.depends("fiscal_position_ids")
    def _compute_new_fps_count(self):
        self.new_fps = len(self.fiscal_position_ids.filtered(lambda x: x.type == "new"))

    @api.depends("tax_ids")
    def _compute_updated_taxes_count(self):
        self.updated_taxes = len(self.tax_ids.filtered(lambda x: x.type == "updated"))

    @api.depends("account_ids")
    def _compute_updated_accounts_count(self):
        self.updated_accounts = (
            len(self.account_ids.filtered(lambda x: x.type == "updated"))
            - self.rejected_updated_account_number
        )

    @api.depends("fiscal_position_ids")
    def _compute_updated_fps_count(self):
        self.updated_fps = len(
            self.fiscal_position_ids.filtered(lambda x: x.type == "updated")
        )

    @api.depends("tax_ids")
    def _compute_deleted_taxes_count(self):
        self.deleted_taxes = len(self.tax_ids.filtered(lambda x: x.type == "deleted"))

    @api.onchange("company_id")
    def _onchage_company_update_chart_template(self):
        self.chart_template_id = self.company_id.chart_template_id

    def _reopen(self):
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_id": self.id,
            "res_model": self._name,
            "target": "new",
            # save original model in context,
            # because selecting the list of available
            # templates requires a model in context
            "context": {"default_model": self._name},
        }

    def action_init(self):
        """Initial action that sets the initial state."""
        self.write(
            {
                "state": "init",
                "tax_ids": [(2, r.id, False) for r in self.tax_ids],
                "account_ids": [(2, r.id, False) for r in self.account_ids],
                "fiscal_position_ids": [
                    (2, r.id, False) for r in self.fiscal_position_ids
                ],
            }
        )
        return self._reopen()

    def action_find_records(self):
        """Searchs for records to update/create and shows them."""
        self.clear_caches()
        self = self.with_context(lang=self.lang)
        # Search for, and load, the records to create/update.
        if self.update_tax:
            self._find_taxes()
        if self.update_account:
            self._find_accounts()
        if self.update_fiscal_position:
            self._find_fiscal_positions()
        # Write the results, and go to the next step.
        self.state = "ready"
        return self._reopen()

    def _check_consistency(self):
        """Method for assuring consistency in operations before performing
        them. For now, implemented:

        - If a parent tax is tried to be created, children taxes must be
          also included to be created.

        TODO:

        - Check that needed accounts in taxes/FPs are created at the same time.
        - Check that needed taxes in FPs are created at the same time.
        """
        taxes2create = self.tax_ids.filtered(lambda x: x.type == "new")
        parents2create = taxes2create.filtered(lambda x: x.tax_id.children_tax_ids)
        for parent in parents2create:
            if bool(
                parent.tax_id.children_tax_ids - taxes2create.mapped("tax_id")
            ):  # some children taxes are not included to be added
                raise exceptions.UserError(
                    _(
                        "You have at least one parent tax template (%s) whose "
                        "children taxes are not going to be created. Aborting "
                        "as this will provoke an infinite loop. Please check "
                        "if children have been matched, but not the parent one."
                    )
                    % parent.tax_id.name
                )

    def action_update_records(self):
        """Action that creates/updates/deletes the selected elements."""
        self._check_consistency()
        self = self.with_context(lang=self.lang)
        self.rejected_new_account_number = 0
        self.rejected_updated_account_number = 0
        with closing(StringIO()) as log_output:
            handler = logging.StreamHandler(log_output)
            _logger.addHandler(handler)
            # Create or update the records.
            if self.update_tax:
                todo_dict = self._update_taxes()
            perform_rest = True
            if self.update_account:
                self._update_accounts()
                if (
                    EXCEPTION_TEXT in log_output.getvalue()
                    and not self.continue_on_errors
                ):  # Abort early
                    perform_rest = False
            # Clear this cache for avoiding incorrect account hits (as it was
            # queried before account creation)
            self.find_account_by_templates.clear_cache(self)
            if self.update_tax and perform_rest:
                self._update_taxes_pending_for_accounts(todo_dict)
            if self.update_fiscal_position and perform_rest:
                self._update_fiscal_positions()
            # Store new chart in the company
            self.company_id.chart_template_id = self.chart_template_id
            _logger.removeHandler(handler)
            self.log = log_output.getvalue()
        # Check if errors where detected and wether we should stop.
        if EXCEPTION_TEXT in self.log and not self.continue_on_errors:
            raise exceptions.UserError(
                _("One or more errors detected!\n\n%s") % self.log
            )
        # Store the data and go to the next step.
        self.state = "done"
        return self._reopen()

    def _get_real_xml_name(self, template):
        [external_id] = template.get_external_id().values()
        (name, module) = external_id.split(".")
        return "%s.%d_%s" % (name, self.company_id.id, module)

    @tools.ormcache("templates")
    def find_taxes_by_templates(self, templates):
        tax_ids = []
        for tax in templates:
            tax_ids.append(self.find_tax_by_templates(tax))
        return self.env["account.tax"].browse(tax_ids)

    @tools.ormcache("templates")
    def find_tax_by_templates(self, templates):
        """Find a tax that matches the template."""
        # search inactive taxes too, to avoid re-creating
        # taxes that have been deactivated before
        tax_model = self.env["account.tax"].with_context(active_test=False)
        for template in templates:
            for matching in self.tax_matching_ids.sorted("sequence"):
                if matching.matching_value == "xml_id":
                    real = self.env.ref(
                        self._get_real_xml_name(template), raise_if_not_found=False
                    )
                    if not real:
                        continue
                    criteria = ("id", "=", real.id)
                else:
                    field_name = matching.matching_value
                    if not template[field_name]:
                        continue
                    criteria = (field_name, "=", template[field_name])

                result = tax_model.search(
                    [
                        criteria,
                        ("company_id", "=", self.company_id.id),
                        ("type_tax_use", "=", template.type_tax_use),
                    ],
                    limit=1,
                )
                if result:
                    return result.id

        return False

    @tools.ormcache("templates", "current_repartition")
    def find_repartition_by_templates(
        self, templates, current_repartition, tax, inverse_name
    ):
        upd_acc = self.update_tax_repartition_line_account
        upd_tags = self.update_tax_repartition_line_tags
        result = []
        existing_ids = []
        for i, tpl in enumerate(templates):
            factor_percent = tpl.factor_percent
            repartition_type = tpl.repartition_type
            account_id = self.find_account_by_templates(tpl.account_id)
            tags = self.env["account.account.tag"]
            tags += tpl.plus_report_line_ids.mapped("tag_ids").filtered(
                lambda x: not x.tax_negate
            )
            tags += tpl.minus_report_line_ids.mapped("tag_ids").filtered(
                lambda x: x.tax_negate
            )
            tags += tpl.tag_ids
            existing = self.env["account.tax.repartition.line"]
            existing_candidates = current_repartition.filtered(
                lambda r: r.factor_percent == factor_percent
                and r.repartition_type == repartition_type
            )
            if len(existing_candidates) == 1:
                existing = existing_candidates
            elif len(existing_candidates) > 1:
                # We may have this situation in case of e.g. 50%/50% on tax.
                # In this case we assume that the repartition line order
                # is the same between templates and actual tax objects
                existing_candidate = current_repartition[i]
                if existing_candidate in existing_candidates:
                    existing = existing_candidate

            if existing:
                existing_ids.append(existing.id)
                upd_vals = {}
                if upd_acc and existing.account_id.id != account_id:
                    upd_vals["account_id"] = account_id
                if upd_tags:
                    if existing.tag_ids != tags:
                        upd_vals["tag_ids"] = [(6, 0, tags.ids)]
                if upd_vals:
                    # update record
                    result.append((1, existing.id, upd_vals))
            if not existing:
                # create a new mapping
                result.append(
                    (
                        0,
                        0,
                        {
                            inverse_name: tax.id,
                            "factor_percent": factor_percent,
                            "repartition_type": repartition_type,
                            "account_id": account_id,
                            "tag_ids": [(6, 0, tags.ids)],
                        },
                    )
                )

        # Mark to be removed the lines not found
        remove_ids = [x for x in current_repartition.ids if x not in existing_ids]
        result += [(2, x) for x in remove_ids]
        return result

    @api.model
    @tools.ormcache("code")
    def padded_code(self, code):
        """Return a right-zero-padded code with the chosen digits."""
        return code.ljust(self.code_digits, "0")

    @tools.ormcache("templates")
    def find_accounts_by_templates(self, templates):
        account_ids = []
        for account in templates:
            account_ids.append(self.find_tax_by_templates(account))
        return self.env["account.account"].browse(account_ids)

    @tools.ormcache("templates")
    def find_account_by_templates(self, templates):
        """Find an account that matches the template."""
        account_model = self.env["account.account"]
        for matching in self.account_matching_ids.sorted("sequence"):
            if matching.matching_value == "xml_id":
                real = self.env["account.account"]
                for template in templates:
                    try:
                        real |= self.env.ref(self._get_real_xml_name(template))
                    except BaseException:
                        pass

                if not real:
                    continue
                criteria = ("id", "in", real.ids)
            elif matching.matching_value == "code":
                codes = templates.mapped("code")
                if not codes:
                    continue
                criteria = ("code", "in", list(map(self.padded_code, codes)))
            else:
                field_name = matching.matching_value
                field_values = templates.mapped(field_name)
                if not field_values:
                    continue
                criteria = (field_name, "in", field_values)

            result = account_model.search(
                [criteria, ("company_id", "=", self.company_id.id)]
            )
            if result:
                return result.id

        return False

    @tools.ormcache("templates")
    def find_fp_by_templates(self, templates):
        """Find a real fiscal position from a template."""
        fp_model = self.env["account.fiscal.position"]
        for matching in self.fp_matching_ids.sorted("sequence"):
            if matching.matching_value == "xml_id":
                real = self.env["account.fiscal.position"]
                for template in templates:
                    try:
                        real |= self.env.ref(self._get_real_xml_name(template))
                    except BaseException:
                        pass

                if not real:
                    continue
                criteria = ("id", "in", real.ids)
            else:
                field_name = matching.matching_value
                field_values = templates.mapped(field_name)
                if not field_values:
                    continue
                criteria = (field_name, "in", field_values)

            result = fp_model.search(
                [criteria, ("company_id", "=", self.company_id.id)], limit=1
            )
            if result:
                return result.id

        return False

    @tools.ormcache("templates", "current_fp_accounts")
    def find_fp_account_by_templates(self, templates, current_fp_accounts):
        result = []
        for tpl in templates:
            pos_id = self.find_fp_by_templates(tpl.position_id)
            src_id = self.find_account_by_templates(tpl.account_src_id)
            dest_id = self.find_account_by_templates(tpl.account_dest_id)
            existing = self.env["account.fiscal.position.account"].search(
                [
                    ("position_id", "=", pos_id),
                    ("account_src_id", "=", src_id),
                    ("account_dest_id", "=", dest_id),
                ]
            )
            if not existing:
                # create a new mapping
                result.append(
                    (
                        0,
                        0,
                        {
                            "position_id": pos_id,
                            "account_src_id": src_id,
                            "account_dest_id": dest_id,
                        },
                    )
                )
            else:
                current_fp_accounts -= existing
        # Mark to be removed the lines not found
        if current_fp_accounts:
            result += [(2, x.id) for x in current_fp_accounts]
        return result

    @tools.ormcache("templates", "current_fp_taxes")
    def find_fp_tax_by_templates(self, templates, current_fp_taxes):
        result = []
        for tpl in templates:
            pos_id = self.find_fp_by_templates(tpl.position_id)
            src_id = self.find_tax_by_templates(tpl.tax_src_id)
            dest_id = self.find_tax_by_templates(tpl.tax_dest_id)
            existing = self.env["account.fiscal.position.tax"].search(
                [
                    ("position_id", "=", pos_id),
                    ("tax_src_id", "=", src_id),
                    ("tax_dest_id", "=", dest_id),
                ]
            )
            if not existing:
                # create a new mapping
                result.append(
                    (
                        0,
                        0,
                        {
                            "position_id": pos_id,
                            "tax_src_id": src_id,
                            "tax_dest_id": dest_id,
                        },
                    )
                )
            else:
                current_fp_taxes -= existing
        # Mark to be removed the lines not found
        if current_fp_taxes:
            result += [(2, x.id) for x in current_fp_taxes]
        return result

    @api.model
    @tools.ormcache("name")
    def fields_to_ignore(self, name):
        """Get fields that will not be used when checking differences.

        :param str template: A template record.
        :param str name: The name of the template model.
        :return set: Fields to ignore in diff.
        """
        specials_mapping = {
            "account.tax.template": {"chart_template_id", "children_tax_ids"},
            "account.account.template": {"chart_template_id", "root_id", "nocreate"},
            "account.fiscal.position.template": {"chart_template_id"},
        }
        specials = {
            "display_name",
            "__last_update",
            "company_id",
        } | specials_mapping.get(name, set())
        return set(models.MAGIC_COLUMNS) | specials

    @api.model
    def diff_fields(self, template, real):
        """Get fields that are different in template and real records.

        :param odoo.models.Model template:
            Template record.
        :param odoo.models.Model real:
            Real record.

        :return dict:
            Fields that are different in both records, and the expected value.
        """
        result = dict()
        ignore = self.fields_to_ignore(template._name)
        template_field_mapping = {
            "account.tax.template": self.tax_field_ids,
            "account.account.template": self.account_field_ids,
            "account.fiscal.position.template": self.fp_field_ids,
        }
        to_include = template_field_mapping[template._name].mapped("name")
        for key, field in template._fields.items():
            if key in ignore or key not in to_include or not hasattr(real, key):
                continue
            expected = None
            # Translate template records to reals for comparison
            relation = field.get_description(self.env).get("relation", "")
            if relation:
                if relation == "account.tax.template":
                    expected = self.find_taxes_by_templates(template[key])
                elif relation == "account.account.template":
                    expected = self.find_accounts_by_templates(template[key])
                elif relation == "account.fiscal.position.tax.template":
                    expected = self.find_fp_tax_by_templates(template[key], real[key])
                elif relation == "account.fiscal.position.account.template":
                    expected = self.find_fp_account_by_templates(
                        template[key], real[key]
                    )
                elif relation == "account.tax.repartition.line.template":
                    expected = self.find_repartition_by_templates(
                        template[key], real[key], real, field.inverse_name
                    )
            # Register detected differences
            if expected is not None:
                if expected != [] and (
                    key
                    in ["invoice_repartition_line_ids", "refund_repartition_line_ids"]
                    or expected != real[key]
                ):
                    result[key] = expected
            else:
                template_value = template[key]
                if template._name == "account.account.template" and key == "code":
                    template_value = self.padded_code(template["code"])
                if template_value != real[key]:
                    result[key] = template_value
            # Avoid to cache recordset references
            if key in result:
                if isinstance(real._fields[key], fields.Many2many):
                    result[key] = [(6, 0, result[key].ids)]
                elif isinstance(real._fields[key], fields.Many2one):
                    result[key] = result[key].id
        return result

    @api.model
    def diff_notes(self, template, real):
        """Get notes for humans on why is this record going to be updated.

        :param openerp.models.Model template:
            Template record.

        :param openerp.models.Model real:
            Real record.

        :return str:
            Notes result.
        """
        result = list()
        different_fields = sorted(
            template._fields[f].get_description(self.env)["string"]
            for f in self.diff_fields(template, real).keys()
        )
        if different_fields:
            result.append(
                _("Differences in these fields: %s.") % ", ".join(different_fields)
            )
            # Special for taxes
            if template._name == "account.tax.template":
                if not real.active:
                    result.append(_("Tax is disabled."))
        return "\n".join(result)

    @tools.ormcache("self", "template", "real_obj")
    def missing_xml_id(self, template, real_obj):
        ir_model_data = self.env["ir.model.data"]
        template_xmlid = ir_model_data.search(
            [("model", "=", template._name), ("res_id", "=", template.id)]
        )
        new_xml_id = "%d_%s" % (self.company_id.id, template_xmlid.name)
        return not ir_model_data.search(
            [
                ("res_id", "=", real_obj.id),
                ("model", "=", real_obj._name),
                ("module", "=", template_xmlid.module),
                ("name", "=", new_xml_id),
            ]
        )

    def _find_taxes(self):
        """Search for, and load, tax templates to create/update/delete."""
        found_taxes_ids = []
        self.tax_ids.unlink()
        # Search for changes between template and real tax
        for template in self.chart_template_ids.with_context(active_test=False).mapped(
            "tax_template_ids"
        ):
            # Check if the template matches a real tax
            tax_id = self.find_tax_by_templates(template)
            if not tax_id:
                # Tax to be created
                self.tax_ids.create(
                    {
                        "tax_id": template.id,
                        "update_chart_wizard_id": self.id,
                        "type": "new",
                        "notes": _("Name or description not found."),
                    }
                )
            else:
                found_taxes_ids.append(tax_id)
                # Check the tax for changes
                tax = self.env["account.tax"].browse(tax_id)
                notes = self.diff_notes(template, tax)

                if self.recreate_xml_ids and self.missing_xml_id(template, tax):
                    notes += (notes and "\n" or "") + _("Missing XML-ID.")

                if notes:
                    # Tax to be updated
                    self.tax_ids.create(
                        {
                            "tax_id": template.id,
                            "update_chart_wizard_id": self.id,
                            "type": "updated",
                            "update_tax_id": tax_id,
                            "notes": notes,
                        }
                    )
        # search for taxes not in the template and propose them for
        # deactivation
        taxes_to_deactivate = self.env["account.tax"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("id", "not in", found_taxes_ids),
                ("active", "=", True),
            ]
        )
        for tax in taxes_to_deactivate:
            self.tax_ids.create(
                {
                    "update_chart_wizard_id": self.id,
                    "type": "deleted",
                    "update_tax_id": tax.id,
                    "notes": _("To deactivate: not in the template"),
                }
            )

    def _find_accounts(self):
        """Load account templates to create/update."""
        self.account_ids.unlink()
        for template in self.chart_template_ids.mapped("account_ids"):
            # Search for a real account that matches the template
            account_id = self.find_account_by_templates(template)
            if not account_id:
                # Account to be created
                self.account_ids.create(
                    {
                        "account_id": template.id,
                        "update_chart_wizard_id": self.id,
                        "type": "new",
                        "notes": _("No account found with this code."),
                    }
                )
            else:
                # Check the account for changes
                account = self.env["account.account"].browse(account_id)
                notes = self.diff_notes(template, account)

                if self.recreate_xml_ids and self.missing_xml_id(template, account):
                    notes += (notes and "\n" or "") + _("Missing XML-ID.")

                if notes:
                    # Account to be updated
                    self.account_ids.create(
                        {
                            "account_id": template.id,
                            "update_chart_wizard_id": self.id,
                            "type": "updated",
                            "update_account_id": account_id,
                            "notes": notes,
                        }
                    )

    def _find_fiscal_positions(self):
        """Load fiscal position templates to create/update."""
        wiz_fp = self.env["wizard.update.charts.accounts.fiscal.position"]
        self.fiscal_position_ids.unlink()

        # Search for new / updated fiscal positions
        templates = self.env["account.fiscal.position.template"].search(
            [("chart_template_id", "in", self.chart_template_ids.ids)]
        )
        for template in templates:
            # Search for a real fiscal position that matches the template
            fp_id = self.find_fp_by_templates(template)
            if not fp_id:
                # Fiscal position to be created
                wiz_fp.create(
                    {
                        "fiscal_position_id": template.id,
                        "update_chart_wizard_id": self.id,
                        "type": "new",
                        "notes": _("No fiscal position found with this name."),
                    }
                )
            else:
                # Check the fiscal position for changes
                fp = self.env["account.fiscal.position"].browse(fp_id)
                notes = self.diff_notes(template, fp)

                if self.recreate_xml_ids and self.missing_xml_id(template, fp):
                    notes += (notes and "\n" or "") + _("Missing XML-ID.")

                if notes:
                    # Fiscal position template to be updated
                    wiz_fp.create(
                        {
                            "fiscal_position_id": template.id,
                            "update_chart_wizard_id": self.id,
                            "type": "updated",
                            "update_fiscal_position_id": fp_id,
                            "notes": notes,
                        }
                    )

    def recreate_xml_id(self, template, real_obj):
        ir_model_data = self.env["ir.model.data"]
        template_xmlid = ir_model_data.search(
            [("model", "=", template._name), ("res_id", "=", template.id)]
        )
        new_xml_id = "%d_%s" % (self.company_id.id, template_xmlid.name)
        ir_model_data.search(
            [("model", "=", real_obj._name), ("res_id", "=", real_obj.id)]
        ).unlink()
        template_xmlid.copy(
            {
                "model": real_obj._name,
                "res_id": real_obj.id,
                "name": new_xml_id,
                "noupdate": True,
            }
        )

    def _update_taxes(self):
        """Process taxes to create/update/deactivate."""
        # First create taxes in batch
        taxes_to_create = self.tax_ids.filtered(lambda x: x.type == "new")
        todo_dict = taxes_to_create.mapped("tax_id")._generate_tax(self.company_id)
        for wiz_tax in taxes_to_create:
            new_tax = self.env["account.tax"].browse(
                todo_dict["tax_template_to_tax"][wiz_tax.tax_id.id]
            )
            _logger.info(
                _("Created tax %s."), "'{}' (ID:{})".format(new_tax.name, new_tax.id)
            )
        for wiz_tax in self.tax_ids.filtered(lambda x: x.type != "new"):
            template, tax = wiz_tax.tax_id, wiz_tax.update_tax_id
            # Deactivate tax
            if wiz_tax.type == "deleted":
                tax.active = False
                _logger.info(_("Deactivated tax %s."), "'%s'" % tax.name)
                continue
            else:
                updated = False
                for key, value in self.diff_fields(template, tax).items():
                    # We defer update because account might not be created yet
                    if key in [
                        "cash_basis_transition_account_id",
                        "invoice_repartition_line_ids",
                        "refund_repartition_line_ids",
                    ]:
                        continue
                    tax[key] = value
                    updated = True
                if updated:
                    _logger.info(_("Updated tax %s."), "'%s'" % template.name)
                if self.recreate_xml_ids and self.missing_xml_id(template, tax):
                    self.recreate_xml_id(template, tax)
                    _logger.info(
                        _("Updated tax %s. (Recreated XML-IDs)"), "'%s'" % template.name
                    )
        return todo_dict

    def _update_accounts(self):
        """Process accounts to create/update."""
        for wiz_account in self.account_ids:
            account, template = (wiz_account.update_account_id, wiz_account.account_id)
            if wiz_account.type == "new":
                # Create the account
                tax_template_ref = {
                    tax.id: self.find_tax_by_templates(tax) for tax in template.tax_ids
                }
                vals = self.chart_template_id._get_account_vals(
                    self.company_id,
                    template,
                    self.padded_code(template.code),
                    tax_template_ref,
                )
                try:
                    with self.env.cr.savepoint():
                        self.chart_template_id.create_record_with_xmlid(
                            self.company_id, template, "account.account", vals
                        )
                        _logger.info(
                            _("Created account %s."),
                            "'{} - {}'".format(vals["code"], vals["name"]),
                        )
                except Exception:
                    self.rejected_new_account_number += 1
                    if config["test_enable"]:
                        _logger.info(EXCEPTION_TEXT)
                    else:  # pragma: no cover
                        _logger.exception(
                            "ERROR: " + _("Exception creating account %s."),
                            "'{} - {}'".format(template.code, template.name),
                        )
                    if not self.continue_on_errors:
                        break
            else:
                # Update the account
                try:
                    with self.env.cr.savepoint():
                        for key, value in iter(
                            self.diff_fields(template, account).items()
                        ):
                            account[key] = value
                            _logger.info(
                                _("Updated account %s."),
                                "'{} - {}'".format(account.code, account.name),
                            )
                        if self.recreate_xml_ids and self.missing_xml_id(
                            template, account
                        ):
                            self.recreate_xml_id(template, account)
                            _logger.info(
                                _("Updated account %s. (Recreated XML-ID)"),
                                "'{} - {}'".format(account.code, account.name),
                            )

                except Exception:
                    self.rejected_updated_account_number += 1
                    if config["test_enable"]:
                        _logger.info(EXCEPTION_TEXT)
                    else:  # pragma: no cover
                        _logger.exception(
                            "ERROR: " + _("Exception writing account %s."),
                            "'{} - {}'".format(account.code, account.name),
                        )
                    if not self.continue_on_errors:
                        break

    def _update_taxes_pending_for_accounts(self, todo_dict):
        """Updates the taxes (created or updated on previous steps) to set
        the references to the accounts (the taxes where created/updated first,
        when the referenced accounts are still not available).
        """
        done = self.env["account.tax"]
        for k, v in todo_dict["account_dict"]["account.tax"].items():
            vals = {}
            for fld in [
                "cash_basis_transition_account_id",
            ]:
                if v[fld]:
                    acc_id = self.find_account_by_templates(
                        self.env["account.account.template"].browse(v[fld])
                    )
                    if acc_id:
                        vals[fld] = acc_id
                    else:
                        raise exceptions.UserError(
                            _("No real account found for template account with ID %s")
                            % v[fld]
                        )
            if vals:
                tax = self.env["account.tax"].browse(k)
                tax.write(vals)
                done |= tax

        for k, v in todo_dict["account_dict"]["account.tax.repartition.line"].items():
            if v["account_id"]:
                rep_line = self.env["account.tax.repartition.line"].browse(k)
                acc_id = self.find_account_by_templates(
                    self.env["account.account.template"].browse(v["account_id"])
                )
                if acc_id:
                    rep_line.write({"account_id": acc_id})
                    done |= rep_line.invoice_tax_id or rep_line.refund_tax_id
                else:
                    raise exceptions.UserError(
                        _("No real account found for template account with ID %s")
                        % v["account_id"]
                    )

        for wiz_tax in self.tax_ids.filtered(lambda r: r.type == "updated"):
            template = wiz_tax.tax_id
            tax = wiz_tax.update_tax_id
            vals = {}
            for key, value in self.diff_fields(template, tax).items():
                if key in {
                    "cash_basis_transition_account_id",
                    "invoice_repartition_line_ids",
                    "refund_repartition_line_ids",
                }:
                    vals[key] = value
            if vals:
                tax.write(vals)
                done |= tax

        if done:
            _logger.info(
                _("Post-updated account fields for taxes with IDs %s."), "%s" % done.ids
            )

    def _prepare_fp_vals(self, fp_template):
        # Tax mappings
        tax_mapping = []
        for fp_tax in fp_template.tax_ids:
            # Create the fp tax mapping
            tax_mapping.append(
                {
                    "tax_src_id": self.find_tax_by_templates(fp_tax.tax_src_id),
                    "tax_dest_id": self.find_tax_by_templates(fp_tax.tax_dest_id),
                }
            )
        # Account mappings
        account_mapping = []
        for fp_account in fp_template.account_ids:
            # Create the fp account mapping
            account_mapping.append(
                {
                    "account_src_id": (
                        self.find_account_by_templates(fp_account.account_src_id)
                    ),
                    "account_dest_id": (
                        self.find_account_by_templates(fp_account.account_dest_id)
                    ),
                }
            )
        return {
            "company_id": self.company_id.id,
            "name": fp_template.name,
            "tax_ids": [(0, 0, x) for x in tax_mapping],
            "account_ids": [(0, 0, x) for x in account_mapping],
        }

    def _update_fiscal_positions(self):
        """Process fiscal position templates to create/update."""
        for wiz_fp in self.fiscal_position_ids:
            fp, template = (wiz_fp.update_fiscal_position_id, wiz_fp.fiscal_position_id)
            if wiz_fp.type == "new":
                # Create a new fiscal position
                self.chart_template_id.create_record_with_xmlid(
                    self.company_id,
                    template,
                    "account.fiscal.position",
                    self._prepare_fp_vals(template),
                )
                _logger.info(_("Created fiscal position %s."), "'%s'" % template.name)
            else:
                for key, value in self.diff_fields(template, fp).items():
                    fp[key] = value
                    _logger.info(
                        _("Updated fiscal position %s."), "'%s'" % template.name
                    )

                if self.recreate_xml_ids and self.missing_xml_id(template, fp):
                    self.recreate_xml_id(template, fp)
                    _logger.info(
                        _("Updated fiscal position %s. (Recreated XML-ID)"),
                        "'%s'" % template.name,
                    )


class WizardUpdateChartsAccountsTax(models.TransientModel):
    _name = "wizard.update.charts.accounts.tax"
    _description = "Tax that needs to be updated (new or updated in the " "template)."

    tax_id = fields.Many2one(
        comodel_name="account.tax.template", string="Tax template", ondelete="set null"
    )
    update_chart_wizard_id = fields.Many2one(
        comodel_name="wizard.update.charts.accounts",
        string="Update chart wizard",
        required=True,
        ondelete="cascade",
    )
    type = fields.Selection(
        selection=[
            ("new", "New template"),
            ("updated", "Updated template"),
            ("deleted", "Tax to deactivate"),
        ],
        string="Type",
        readonly=False,
    )
    type_tax_use = fields.Selection(related="tax_id.type_tax_use", readonly=True)
    update_tax_id = fields.Many2one(
        comodel_name="account.tax",
        string="Tax to update",
        required=False,
        ondelete="set null",
    )
    notes = fields.Text("Notes", readonly=True)
    recreate_xml_ids = fields.Boolean(
        string="Recreate missing XML-IDs",
        related="update_chart_wizard_id.recreate_xml_ids",
    )


class WizardUpdateChartsAccountsAccount(models.TransientModel):
    _name = "wizard.update.charts.accounts.account"
    _description = (
        "Account that needs to be updated (new or updated in the " "template)."
    )

    account_id = fields.Many2one(
        comodel_name="account.account.template",
        string="Account template",
        required=True,
    )
    update_chart_wizard_id = fields.Many2one(
        comodel_name="wizard.update.charts.accounts",
        string="Update chart wizard",
        required=True,
        ondelete="cascade",
    )
    type = fields.Selection(
        selection=[("new", "New template"), ("updated", "Updated template")],
        string="Type",
        readonly=False,
    )
    update_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Account to update",
        required=False,
        ondelete="set null",
    )
    notes = fields.Text("Notes", readonly=True)
    recreate_xml_ids = fields.Boolean(
        string="Recreate missing XML-IDs",
        related="update_chart_wizard_id.recreate_xml_ids",
    )


class WizardUpdateChartsAccountsFiscalPosition(models.TransientModel):
    _name = "wizard.update.charts.accounts.fiscal.position"
    _description = (
        "Fiscal position that needs to be updated (new or updated " "in the template)."
    )

    fiscal_position_id = fields.Many2one(
        comodel_name="account.fiscal.position.template",
        string="Fiscal position template",
        required=True,
    )
    update_chart_wizard_id = fields.Many2one(
        comodel_name="wizard.update.charts.accounts",
        string="Update chart wizard",
        required=True,
        ondelete="cascade",
    )
    type = fields.Selection(
        selection=[("new", "New template"), ("updated", "Updated template")],
        string="Type",
        readonly=False,
    )
    update_fiscal_position_id = fields.Many2one(
        comodel_name="account.fiscal.position",
        required=False,
        string="Fiscal position to update",
        ondelete="set null",
    )
    notes = fields.Text("Notes", readonly=True)
    recreate_xml_ids = fields.Boolean(
        string="Recreate missing XML-IDs",
        related="update_chart_wizard_id.recreate_xml_ids",
    )


class WizardMatching(models.TransientModel):
    _name = "wizard.matching"
    _description = "Wizard Matching"
    _order = "sequence"

    update_chart_wizard_id = fields.Many2one(
        comodel_name="wizard.update.charts.accounts",
        string="Update chart wizard",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(required=True, default=1)
    matching_value = fields.Selection(selection="_get_matching_selection")

    def _get_matching_selection(self):
        return [("xml_id", "XML-ID")]

    def _selection_from_files(self, model_name, field_opts):
        result = []
        for opt in field_opts:
            model = self.env[model_name]
            desc = model._fields[opt].get_description(self.env)["string"]
            result.append((opt, "{} ({})".format(desc, opt)))
        return result


class WizardTaxMatching(models.TransientModel):
    _name = "wizard.tax.matching"
    _description = "Wizard Tax Matching"
    _inherit = "wizard.matching"

    def _get_matching_selection(self):
        vals = super(WizardTaxMatching, self)._get_matching_selection()
        vals += self._selection_from_files(
            "account.tax.template", ["description", "name"]
        )
        return vals


class WizardAccountMatching(models.TransientModel):
    _name = "wizard.account.matching"
    _description = "Wizard Account Matching"
    _inherit = "wizard.matching"

    def _get_matching_selection(self):
        vals = super(WizardAccountMatching, self)._get_matching_selection()
        vals += self._selection_from_files("account.account.template", ["code", "name"])
        return vals


class WizardFpMatching(models.TransientModel):
    _name = "wizard.fp.matching"
    _description = "Wizard Fiscal Position Matching"
    _inherit = "wizard.matching"

    def _get_matching_selection(self):
        vals = super(WizardFpMatching, self)._get_matching_selection()
        vals += self._selection_from_files("account.fiscal.position.template", ["name"])
        return vals
