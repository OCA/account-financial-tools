# Copyright 2010 Jordi Esteve, Zikzakmedia S.L. (http://www.zikzakmedia.com)
# Copyright 2010 Pexego Sistemas Informáticos S.L.(http://www.pexego.es)
#        Borja López Soilán
# Copyright 2013 Joaquin Gutierrez (http://www.gutierrezweb.es)
# Copyright 2015 Tecnativa - Antonio Espinosa
# Copyright 2016 Tecnativa - Jairo Llopis
# Copyright 2016 Jacques-Etienne Baudoux <je@bcim.be>
# Copyright 2018 Tecnativa - Pedro M. Baeza
# Copyright 2020 Noviat - Luc De Meyer
# Copyright 2024-2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models, tools

_logger = logging.getLogger(__name__)


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
    chart_template = fields.Selection(
        selection="_chart_template_selection",
        required=True,
    )
    code_digits = fields.Integer()
    update_tax = fields.Boolean(
        string="Update taxes",
        default=True,
        help="Existing taxes are updated. Taxes are searched by name.",
    )
    update_account = fields.Boolean(
        string="Update accounts",
        default=True,
        help="Existing accounts are updated. Accounts are searched by code.",
    )
    update_account_group = fields.Boolean(
        string="Update account groups",
        default=True,
        help="Existing account groups are updated. "
        "Account groups are searched by prefix_code_start.",
    )
    update_fiscal_position = fields.Boolean(
        string="Update fiscal positions",
        default=True,
        help="Existing fiscal positions are updated. Fiscal positions are "
        "searched by name.",
    )
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
    account_group_ids = fields.One2many(
        comodel_name="wizard.update.charts.accounts.account.group",
        inverse_name="update_chart_wizard_id",
        string="Account Groups",
    )
    fiscal_position_ids = fields.One2many(
        comodel_name="wizard.update.charts.accounts.fiscal.position",
        inverse_name="update_chart_wizard_id",
        string="Fiscal positions",
    )
    new_taxes = fields.Integer(compute="_compute_new_taxes_count")
    new_accounts = fields.Integer(compute="_compute_new_accounts_count")
    new_account_groups = fields.Integer(compute="_compute_new_account_groups_count")
    rejected_new_account_number = fields.Integer()
    new_fps = fields.Integer(
        string="New fiscal positions", compute="_compute_new_fps_count"
    )
    updated_taxes = fields.Integer(compute="_compute_updated_taxes_count")
    rejected_updated_account_number = fields.Integer()
    updated_accounts = fields.Integer(compute="_compute_updated_accounts_count")
    updated_account_groups = fields.Integer(
        compute="_compute_updated_account_groups_count"
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
    account_group_field_ids = fields.Many2many(
        comodel_name="ir.model.fields",
        relation="wizard_update_charts_account_group_fields_rel",
        string="Account groups fields",
        domain=lambda self: self._domain_account_group_field_ids(),
        default=lambda self: self._default_account_group_field_ids(),
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
    account_group_matching_ids = fields.One2many(
        comodel_name="wizard.account.group.matching",
        inverse_name="update_chart_wizard_id",
        string="Account groups matching",
        default=lambda self: self._default_account_group_matching_ids(),
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
        return self._domain_per_name("account.tax")

    def _domain_account_field_ids(self):
        return self._domain_per_name("account.account")

    def _domain_account_group_field_ids(self):
        return self._domain_per_name("account.group")

    def _domain_fp_field_ids(self):
        return self._domain_per_name("account.fiscal.position")

    def _default_tax_field_ids(self):
        return [
            (4, x.id)
            for x in self.env["ir.model.fields"].search(
                self._domain_tax_field_ids() + [("ttype", "!=", "one2many")],
            )
        ]

    def _default_account_field_ids(self):
        return [
            (4, x.id)
            for x in self.env["ir.model.fields"].search(
                self._domain_account_field_ids() + [("ttype", "!=", "one2many")],
            )
        ]

    def _default_account_group_field_ids(self):
        return [
            (4, x.id)
            for x in self.env["ir.model.fields"].search(
                self._domain_account_group_field_ids()
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

    def _default_account_group_matching_ids(self):
        ordered_opts = ["xml_id", "code_prefix_start"]
        return self._get_matching_ids("wizard.account.group.matching", ordered_opts)

    def _chart_template_selection(self):
        return (
            self.env["account.chart.template"]
            .with_context(chart_template_only_installed=True)
            ._select_chart_template(self.company_id.country_id)
        )

    @api.depends("tax_ids")
    def _compute_new_taxes_count(self):
        self.new_taxes = len(self.tax_ids.filtered(lambda x: x.type == "new"))

    @api.depends("account_ids")
    def _compute_new_accounts_count(self):
        self.new_accounts = (
            len(self.account_ids.filtered(lambda x: x.type == "new"))
            - self.rejected_new_account_number
        )

    @api.depends("account_group_ids")
    def _compute_new_account_groups_count(self):
        self.new_account_groups = len(
            self.account_group_ids.filtered(lambda x: x.type == "new")
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

    @api.depends("account_group_ids")
    def _compute_updated_account_groups_count(self):
        self.updated_account_groups = len(
            self.account_group_ids.filtered(lambda x: x.type == "updated")
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
        self.chart_template = self.company_id.chart_template

    @api.onchange("chart_template")
    def _onchage_chart_template(self):
        if self.chart_template:
            template = self.env["account.chart.template"]
            data = template._get_chart_template_data(self.chart_template)[
                "template_data"
            ]
            self.code_digits = int(data.get("code_digits", 6))

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

    def _get_chart_template_data(self):
        chart_template_model = self.env["account.chart.template"]
        t_data = chart_template_model._get_chart_template_data(self.chart_template)
        model_mapping = {
            "account.tax": self.update_tax,
            "account.account": self.update_account,
            "account.group": self.update_account_group,
            "account.fiscal.position": self.update_fiscal_position,
        }
        langs = self.env["res.lang"].search([])
        for m_name in model_mapping.keys():
            if not model_mapping[m_name]:
                continue
            for _xmlid, r_data in t_data[m_name].items():
                if "__translation_module__" in r_data:
                    for f_name in list(r_data["__translation_module__"].keys()):
                        for lang in langs:
                            field_translation = (
                                chart_template_model._get_field_translation(
                                    r_data, f_name, lang.code
                                )
                            )
                            short_lang = lang.code.split("_")[0]
                            key_lang = f"{f_name}@{short_lang}"
                            if field_translation:
                                r_data[key_lang] = field_translation
                            else:
                                r_data[key_lang] = r_data[f_name]
        return t_data

    def action_find_records(self):
        """Searchs for records to update/create and shows them."""
        self.env.registry.clear_cache()
        t_data = self._get_chart_template_data()
        # Search for, and load, the records to create/update.
        if self.update_tax:
            self._find_taxes(t_data["account.tax"])
        if self.update_account:
            self._find_accounts(t_data["account.account"])
        if self.update_account_group:
            self._find_account_groups(t_data["account.group"])
        if self.update_fiscal_position:
            self._find_fiscal_positions(t_data["account.fiscal.position"])
        # Write the results, and go to the next step.
        self.state = "ready"
        return self._reopen()

    def action_update_records(self):
        """Action that creates/updates/deletes the selected elements."""
        self.rejected_new_account_number = 0
        self.rejected_updated_account_number = 0
        self.log = False
        t_data = self._get_chart_template_data()
        # Create or update the records.
        if self.update_account:
            self._update_accounts(t_data["account.account"])
        if self.update_tax:
            self._update_taxes(t_data["account.tax"])
        if self.update_account_group:
            self._update_account_groups(t_data["account.group"])
        if self.update_fiscal_position:
            self._update_fiscal_positions(t_data["account.fiscal.position"])
        # Store new chart in the company
        self.company_id.chart_template = self.chart_template
        # Store the data and go to the next step.
        self.state = "done"
        return self._reopen()

    @api.model
    @tools.ormcache("code")
    def padded_code(self, code):
        """Return a right-zero-padded code with the chosen digits.
        Similar to what is done in the _pre_load_data() method of chart.template
        """
        return code.ljust(self.code_digits, "0")

    @api.model
    @tools.ormcache("name")
    def fields_to_ignore(self, name):
        """Get fields that will not be used when checking differences.

        :param str template: A template record.
        :param str name: The name of the template model.
        :return set: Fields to ignore in diff.
        """
        mail_thread_fields = set(self.env["mail.thread"]._fields)
        specials_mapping = {
            "account.tax": mail_thread_fields | {"children_tax_ids", "sequence"},
            "account.account": mail_thread_fields
            | {
                "root_id",
            },
            "account.group": {"parent_id", "code_prefix_end"},
            "account.fiscal.position": {
                "sequence",
            },
        }
        specials = {
            "display_name",
            "__last_update",
            "company_id",
        } | specials_mapping.get(name, set())
        return set(models.MAGIC_COLUMNS) | specials

    @api.model
    def diff_fields(self, record_values, real):  # noqa: C901
        """Get fields that are different in record values and real records.

        :param odoo.models.Model record_values:
            Record values values.
        :param odoo.models.Model real:
            Real record.

        :return dict:
            Fields that are different in both records, and the expected value.
        """
        result = dict()
        ignore = self.fields_to_ignore(real._name)
        field_mapping = {
            "account.tax": self.tax_field_ids,
            "account.account": self.account_field_ids,
            "account.group": self.account_group_field_ids,
            "account.fiscal.position": self.fp_field_ids,
        }
        langs = self.env["res.lang"].search([])
        # If the fields to be queried are not mapped, use all of them
        # (example: account.tax.repartition.line).
        if real._name not in field_mapping:
            field_mapping[real._name] = self.env["ir.model.fields"].search(
                self._domain_per_name(real._name)
            )
        fields_by_key = {x.name: x for x in field_mapping[real._name]}
        to_include = field_mapping[real._name].mapped("name")
        for key in record_values.keys():
            if key in ignore or key not in to_include or not record_values.get(key):
                continue
            field = fields_by_key[key]
            record_value, real_value = record_values[key], real[key]
            if real._name == "account.account" and key == "code":
                record_value = self.padded_code(record_value)
                real_value = self.padded_code(real_value)
            # Field ttype conditions
            if field.ttype == "many2many":
                if isinstance(record_value, str):
                    real_xml_ids = []
                    for child_item in real_value:
                        real_xml_ids.append(child_item.get_external_id()[child_item.id])
                    real_xml_id = ",".join(real_xml_ids)
                    if real_xml_id != record_value:
                        result[key] = record_value
                else:
                    record_value_compare = []
                    for record_value_item in record_value:
                        record_value_compare += record_value_item[2]
                    if record_value_compare.sort() != real_value.ids.sort():
                        result[key] = record_value
                continue
            elif field.ttype == "many2one":
                real_xml_id = self._get_external_id(real_value)
                full_xml_id = (
                    f"account.{self.company_id.id}_{record_value}"
                    if "." not in record_value
                    else record_value
                )
                if real_xml_id != full_xml_id:
                    result[key] = record_value
                continue
            elif field.ttype == "one2many":
                if len(record_value) != len(real_value):
                    result[key] = [(5, 0, 0)] + record_value
                else:
                    for key2, record_value_item in enumerate(record_value):
                        res_item = self.diff_fields(
                            record_value_item[2], real_value[key2]
                        )
                        if len(res_item) > 0:
                            # Something has changed in an element, we change everything
                            # just in case (we do not know for sure that the record we
                            # are consulting by key is the correct one, for example,
                            # if it has been deleted by mistake and created again in
                            # the same way).
                            result[key] = [(5, 0, 0)] + record_value
                            break
                continue
            # Define correct value if field is translatable
            if field.translate:
                for lang in langs:
                    short_lang = lang.code.split("_")[0]
                    key_lang = f"{key}@{short_lang}"
                    if key_lang in record_values:
                        real_value_lang = real.with_context(lang=lang.code)[key]
                        record_value_lang = record_values[key_lang]
                        if record_value_lang != real_value_lang:
                            result[key_lang] = record_value_lang
                # print(asass)
            elif record_value != real_value:
                result[key] = record_value
        # __translation_module__
        if len(result.keys()) > 0 and not self.env.context.get("skip_translation_keys"):
            if "__translation_module__" in record_values:
                result["__translation_module__"] = record_values[
                    "__translation_module__"
                ]
        return result

    @api.model
    def diff_notes(self, record_values, real):
        """Get notes for humans on why is this record going to be updated.

        :param openerp.models.Model record_values:
            Record values values.

        :param openerp.models.Model real:
            Real record.

        :return str:
            Notes result.
        """
        result = list()
        different_fields = sorted(
            real._fields[f.split("@")[0] if "@" in f else f].get_description(self.env)[
                "string"
            ]
            for f in self.with_context(skip_translation_keys=True)
            .diff_fields(record_values, real)
            .keys()
        )
        if different_fields:
            result.append(
                _("Differences in these fields: %s.") % ", ".join(different_fields)
            )
        return "\n".join(result)

    def _domain_taxes_to_deactivate(self, found_taxes_ids):
        return [
            ("company_id", "=", self.company_id.id),
            ("id", "not in", found_taxes_ids),
            ("active", "=", True),
        ]

    def _find_record_matching(self, model_name, xmlid, data):
        mapped_fields = {
            "account.account": self.account_matching_ids,
            "account.tax": self.tax_matching_ids,
            "account.group": self.account_group_matching_ids,
            "account.fiscal.position": self.fp_matching_ids,
        }
        company = self.company_id
        model = self.env[model_name]
        company_domain = [("company_id", "=", company.id)]
        for matching in mapped_fields[model_name].sorted("sequence"):
            if matching.matching_value == "xml_id":
                full_xmlid = (
                    f"account.{company.id}_{xmlid}" if "." not in xmlid else xmlid
                )
                record = self.env.ref(full_xmlid, raise_if_not_found=False)
                if record:
                    return record
            else:
                f_name = matching.matching_value
                if not data.get(f_name):
                    continue
                f_value = data[f_name]
                # Fix code from account.account
                if model_name == "account.account" and f_name == "code":
                    f_value = self.padded_code(f_value)
                # Prepare domain
                domain = [(f_name, "=", f_value)] + company_domain
                if model_name == "account.tax" and f_name != "type_tax_use":
                    # Extra domain to prevent find the wrong record
                    domain += [("type_tax_use", "=", data["type_tax_use"])]
                # Search record from model
                result = model.search(domain)
                if result:
                    return result
        return False

    def _get_external_id(self, record):
        return record.get_external_id()[record.id]

    @tools.ormcache("self", "record", "xml_id")
    def missing_xml_id(self, record, xml_id):
        record_xml_id = self._get_external_id(record)
        full_xml_id = (
            f"account.{self.company_id.id}_{xml_id}" if "." not in xml_id else xml_id
        )
        return record_xml_id != full_xml_id

    def recreate_xml_id(self, record, xml_id):
        """Eecreate the xml_id if it is different than expected, otherwise
        chart.template won't do it correctly.
        """
        if self.missing_xml_id(record, xml_id):
            ir_model_data = self.env["ir.model.data"]
            ir_model_data.search(
                [("model", "=", record._name), ("res_id", "=", record.id)]
            ).write(
                {
                    "module": "account",
                    "name": f"{self.company_id.id}_{xml_id}",
                    "noupdate": True,
                }
            )

    def _find_taxes(self, t_data):
        """Search for, and load, template data to create/update/delete."""
        found_taxes_ids = []
        tax_vals = []
        for xmlid, r_data in t_data.items():
            tax = self._find_record_matching("account.tax", xmlid, r_data)
            # Check if the template data matches a real tax
            if not tax:
                # Tax to be created
                tax_vals.append(
                    {
                        "xml_id": xmlid,
                        "type_tax_use": r_data["type_tax_use"],
                        "update_chart_wizard_id": self.id,
                        "type": "new",
                        "notes": _("Name or description not found."),
                    }
                )
            else:
                found_taxes_ids.append(tax.id)
                # Check the tax for changes
                notes = self.diff_notes(r_data, tax)
                if self.missing_xml_id(tax, xmlid):
                    notes += (notes and "\n" or "") + _("Missing XML-ID.")
                if notes:
                    # Tax to be updated
                    tax_vals.append(
                        {
                            "xml_id": xmlid,
                            "type_tax_use": tax.type_tax_use,
                            "update_chart_wizard_id": self.id,
                            "type": "updated",
                            "update_tax_id": tax.id,
                            "notes": notes,
                        }
                    )
        # search for taxes not in the template and propose them for
        # deactivation
        taxes_to_deactivate = self.env["account.tax"].search(
            self._domain_taxes_to_deactivate(found_taxes_ids)
        )
        for tax in taxes_to_deactivate:
            tax_vals.append(
                {
                    "update_chart_wizard_id": self.id,
                    "type_tax_use": tax.type_tax_use,
                    "type": "deleted",
                    "update_tax_id": tax.id,
                    "notes": _("To deactivate: not in the template"),
                }
            )
        self.tax_ids = [(5, 0, 0)] + [(0, 0, tax_val) for tax_val in tax_vals]

    def _find_accounts(self, t_data):
        """Load account template data to create/update."""
        account_vals = []
        for xmlid, r_data in t_data.items():
            account = self._find_record_matching("account.account", xmlid, r_data)
            # Account to be created
            if not account:
                account_vals.append(
                    {
                        "xml_id": xmlid,
                        "update_chart_wizard_id": self.id,
                        "type": "new",
                        "notes": _("No account found with this code."),
                    }
                )
            else:
                # Check the account for changes
                notes = self.diff_notes(r_data, account)
                if self.missing_xml_id(account, xmlid):
                    notes += (notes and "\n" or "") + _("Missing XML-ID.")
                if notes:
                    # Account to be updated
                    account_vals.append(
                        {
                            "xml_id": xmlid,
                            "update_chart_wizard_id": self.id,
                            "type": "updated",
                            "update_account_id": account.id,
                            "notes": notes,
                        }
                    )
        self.account_ids = [(5, 0, 0)] + [(0, 0, a_val) for a_val in account_vals]

    def _find_account_groups(self, t_data):
        """Load account template data to create/update."""
        ag_vals = []
        for xmlid, r_data in t_data.items():
            account_group = self._find_record_matching("account.group", xmlid, r_data)
            if not account_group:
                # Account to be created
                ag_vals.append(
                    {
                        "xml_id": xmlid,
                        "update_chart_wizard_id": self.id,
                        "type": "new",
                        "notes": _("No account found with this code."),
                    }
                )
            else:
                # Check the account for changes
                notes = self.diff_notes(r_data, account_group)
                code_prefix_end = (
                    r_data["code_prefix_end"]
                    if "code_prefix_end" in r_data
                    and r_data["code_prefix_end"] < r_data["code_prefix_start"]
                    else r_data["code_prefix_start"]
                )
                if code_prefix_end != account_group.code_prefix_end:
                    notes += (notes and "\n" or "") + _(
                        "Differences in these fields: %s."
                    ) % r_data["code_prefix_end"]
                if self.missing_xml_id(account_group, xmlid):
                    notes += (notes and "\n" or "") + _("Missing XML-ID.")
                if notes:
                    # Account to be updated
                    ag_vals.append(
                        {
                            "xml_id": xmlid,
                            "update_chart_wizard_id": self.id,
                            "type": "updated",
                            "update_account_group_id": account_group.id,
                            "notes": notes,
                        }
                    )
        self.account_group_ids = [(5, 0, 0)] + [(0, 0, ag_val) for ag_val in ag_vals]

    def _find_fiscal_positions(self, t_data):
        """Load fiscal position template data to create/update."""
        fp_vals = []
        for xmlid, r_data in t_data.items():
            fp = self._find_record_matching("account.fiscal.position", xmlid, r_data)
            if not fp:
                # Fiscal position to be created
                fp_vals.append(
                    {
                        "xml_id": xmlid,
                        "update_chart_wizard_id": self.id,
                        "type": "new",
                        "notes": _("No fiscal position found with this name."),
                    }
                )
            else:
                # Check the fiscal position for changes
                notes = self.diff_notes(r_data, fp)
                if self.missing_xml_id(fp, xmlid):
                    notes += (notes and "\n" or "") + _("Missing XML-ID.")
                if notes:
                    # Fiscal position template to be updated
                    fp_vals.append(
                        {
                            "xml_id": xmlid,
                            "update_chart_wizard_id": self.id,
                            "type": "updated",
                            "update_fiscal_position_id": fp.id,
                            "notes": notes,
                        }
                    )
        self.fiscal_position_ids = [(5, 0, 0)] + [(0, 0, fp_val) for fp_val in fp_vals]

    def _load_data(self, model, data):
        """Process similar to the one in chart template _load() method."""
        template = self.env["account.chart.template"].with_context(
            default_company_id=self.company_id.id,
            allowed_company_ids=[self.company_id.id],
            tracking_disable=True,
            delay_account_group_sync=True,
            # lang="en_US",
        )
        created_records = template._load_data({model: data})[model]
        langs = self.env["res.lang"].search([])
        # Similar and simpler process than what the _load_translations() method does
        for xml_id, record_vals in data.items():
            if "__translation_module__" not in record_vals:
                continue
            translation_vals_lang = {}
            for f_name in record_vals["__translation_module__"].keys():
                for lang in langs:
                    short_lang = lang.code.split("_")[0]
                    key_lang = f"{f_name}@{short_lang}"
                    if key_lang in record_vals:
                        if lang not in translation_vals_lang:
                            translation_vals_lang[lang.code] = {}
                        translation_vals_lang[lang.code][f_name] = record_vals[key_lang]
            if isinstance(xml_id, int):
                record = self.env[model].browse(xml_id)
            else:
                xml_id = f"{('account.' + str(self.company_id.id) + '_') if '.' not in xml_id else ''}{xml_id}"
                record = self.env.ref(xml_id)
            # Updatr translation vals
            for lang in langs:
                if lang.code not in translation_vals_lang:
                    continue
                translation_vals = translation_vals_lang[lang.code]
                record.with_context(lang=lang.code).write(translation_vals)
        for record in created_records:
            msg = _(
                (f"Created/updated {record._name} %s."),
                f"'{record.name}' (ID:{record.id})",
            )
            _logger.info(msg)
            if not self.log:
                self.log = msg
            else:
                self.log += f"\n{msg}"

    def _update_taxes(self, t_data):
        """Process taxes to create/update/deactivate."""
        # First create taxes in batch
        data = {}
        for wiz_tax in self.tax_ids:
            tax = wiz_tax.update_tax_id
            if wiz_tax.type == "deleted":
                tax.active = False
                _logger.info(_("Deactivated tax %s."), "'%s'" % tax.name)
                continue
            xml_id = wiz_tax.xml_id
            key = tax.id or xml_id
            t_data_item = t_data[xml_id]
            data_item = t_data_item if wiz_tax.type == "new" else {}
            if wiz_tax.type == "updated":
                self.recreate_xml_id(tax, xml_id)
                data_item = self.diff_fields(t_data_item, tax)
            # Do not set tax_group_id if it does not exist
            if wiz_tax.type == "new" and "tax_group_id" in data_item:
                tax_group_id_xml_id = data_item["tax_group_id"]
                real_tax_group_xml_id = (
                    f"account.{self.company_id.id}_{tax_group_id_xml_id}"
                )
                if not self.env.ref(real_tax_group_xml_id, raise_if_not_found=False):
                    del data_item["tax_group_id"]
            # Do not set repartition_line_ids lines linked to non-existent accounts
            if wiz_tax.type == "new" and "repartition_line_ids" in data_item:
                new_repartition_line_ids = []
                for line in data_item["repartition_line_ids"]:
                    if "account_id" in line[2]:
                        account_id_xml_id = line[2]["account_id"]
                        real_account_id_xml_id = (
                            f"account.{self.company_id.id}_{account_id_xml_id}"
                        )
                        if self.env.ref(
                            real_account_id_xml_id, raise_if_not_found=False
                        ):
                            new_repartition_line_ids.append(line)
                    else:
                        new_repartition_line_ids.append(line)
                data_item["repartition_line_ids"] = new_repartition_line_ids
            data[key] = data_item
        self._load_data("account.tax", data)

    def _update_accounts(self, t_data):
        """Process accounts to create/update."""
        data = {}
        for wiz_account in self.account_ids:
            account = wiz_account.update_account_id
            xml_id = wiz_account.xml_id
            key = account.id or xml_id
            t_data_item = t_data[xml_id]
            data_item = t_data_item if wiz_account.type == "new" else {}
            if wiz_account.type == "updated":
                self.recreate_xml_id(account, xml_id)
                data_item = self.diff_fields(t_data_item, account)
            data[key] = data_item
        self._load_data("account.account", data)

    def _update_account_groups(self, t_data):
        """Process account groups templates to create/update."""
        data = {}
        for wiz_ag in self.account_group_ids:
            ag = wiz_ag.update_account_group_id
            xml_id = wiz_ag.xml_id
            key = ag.id or xml_id
            t_data_item = t_data[xml_id]
            data_item = t_data_item if wiz_ag.type == "new" else {}
            if wiz_ag.type == "updated":
                self.recreate_xml_id(ag, xml_id)
                data_item = self.diff_fields(t_data_item, ag)
            data[key] = data_item
        self._load_data("account.group", data)

    def _update_fiscal_positions(self, t_data):
        """Process fiscal position templates to create/update."""
        data = {}
        for wiz_fp in self.fiscal_position_ids:
            fp = wiz_fp.update_fiscal_position_id
            xml_id = wiz_fp.xml_id
            key = fp.id or xml_id
            t_data_item = t_data[xml_id]
            data_item = t_data_item if wiz_fp.type == "new" else {}
            if wiz_fp.type == "updated":
                self.recreate_xml_id(fp, xml_id)
                data_item = self.diff_fields(t_data_item, fp)
            data[key] = data_item
        self._load_data("account.fiscal.position", data)


class WizardUpdateChartsAccountsTax(models.TransientModel):
    _name = "wizard.update.charts.accounts.tax"
    _description = "Tax that needs to be updated (new or updated in the " "template)."

    xml_id = fields.Char()
    update_chart_wizard_id = fields.Many2one(
        comodel_name="wizard.update.charts.accounts",
        string="Update chart wizard",
        required=True,
        ondelete="cascade",
    )
    type = fields.Selection(
        selection=[
            ("new", "New tax"),
            ("updated", "Updated tax"),
            ("deleted", "Tax to deactivate"),
        ],
        readonly=False,
    )
    type_tax_use = fields.Selection(
        selection="_get_account_tax_type_tax_uses", readonly=True
    )
    update_tax_id = fields.Many2one(
        comodel_name="account.tax",
        string="Tax to update",
        required=False,
        ondelete="set null",
    )
    notes = fields.Text(readonly=True)

    def _get_account_tax_type_tax_uses(self):
        return self.env["account.tax"].fields_get(allfields=["type_tax_use"])[
            "type_tax_use"
        ]["selection"]


class WizardUpdateChartsAccountsAccount(models.TransientModel):
    _name = "wizard.update.charts.accounts.account"
    _description = (
        "Account that needs to be updated (new or updated in the " "template)."
    )

    xml_id = fields.Char()
    update_chart_wizard_id = fields.Many2one(
        comodel_name="wizard.update.charts.accounts",
        string="Update chart wizard",
        required=True,
        ondelete="cascade",
    )
    type = fields.Selection(
        selection=[("new", "New account"), ("updated", "Updated account")],
        readonly=False,
    )
    update_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Account to update",
        required=False,
        ondelete="set null",
    )
    notes = fields.Text(readonly=True)


class WizardUpdateChartsAccountsAccountGroup(models.TransientModel):
    _name = "wizard.update.charts.accounts.account.group"
    _description = (
        "Account group that needs to be updated (new or updated in the template)."
    )

    xml_id = fields.Char()
    update_chart_wizard_id = fields.Many2one(
        comodel_name="wizard.update.charts.accounts",
        string="Update chart wizard",
        required=True,
        ondelete="cascade",
    )
    type = fields.Selection(
        selection=[("new", "New account group"), ("updated", "Updated accoung group")],
        readonly=False,
    )
    update_account_group_id = fields.Many2one(
        comodel_name="account.group",
        string="Account group to update",
        required=False,
        ondelete="set null",
    )
    notes = fields.Text(readonly=True)


class WizardUpdateChartsAccountsFiscalPosition(models.TransientModel):
    _name = "wizard.update.charts.accounts.fiscal.position"
    _description = (
        "Fiscal position that needs to be updated (new or updated " "in the template)."
    )

    xml_id = fields.Char()
    update_chart_wizard_id = fields.Many2one(
        comodel_name="wizard.update.charts.accounts",
        string="Update chart wizard",
        required=True,
        ondelete="cascade",
    )
    type = fields.Selection(
        selection=[
            ("new", "New fiscal position"),
            ("updated", "Updated fiscal position"),
        ],
        readonly=False,
    )
    update_fiscal_position_id = fields.Many2one(
        comodel_name="account.fiscal.position",
        required=False,
        string="Fiscal position to update",
        ondelete="set null",
    )
    notes = fields.Text(readonly=True)


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
            result.append((opt, f"{desc} ({opt})"))
        return result


class WizardTaxMatching(models.TransientModel):
    _name = "wizard.tax.matching"
    _description = "Wizard Tax Matching"
    _inherit = "wizard.matching"

    def _get_matching_selection(self):
        vals = super()._get_matching_selection()
        vals += self._selection_from_files("account.tax", ["description", "name"])
        return vals


class WizardAccountMatching(models.TransientModel):
    _name = "wizard.account.matching"
    _description = "Wizard Account Matching"
    _inherit = "wizard.matching"

    def _get_matching_selection(self):
        vals = super()._get_matching_selection()
        vals += self._selection_from_files("account.account", ["code", "name"])
        return vals


class WizardFpMatching(models.TransientModel):
    _name = "wizard.fp.matching"
    _description = "Wizard Fiscal Position Matching"
    _inherit = "wizard.matching"

    def _get_matching_selection(self):
        vals = super()._get_matching_selection()
        vals += self._selection_from_files("account.fiscal.position", ["name"])
        return vals


class WizardAccountGroupMatching(models.TransientModel):
    _name = "wizard.account.group.matching"
    _description = "Wizard Account Group Matching"
    _inherit = "wizard.matching"

    def _get_matching_selection(self):
        vals = super()._get_matching_selection()
        vals += self._selection_from_files("account.group", ["code_prefix_start"])
        return vals
