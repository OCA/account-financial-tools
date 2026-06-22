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
from unittest.mock import patch

from odoo import Command, api, fields, models, tools
from odoo.tools.translate import TranslationImporter

_logger = logging.getLogger(__name__)


# HACK https://github.com/odoo/odoo/pull/234333
# If merged upstream, we can remove this class and the patch where it is used.
class _OverwritingTranslationImporter(TranslationImporter):
    def save(self, *args, **kwargs):
        """Always force overwriting existing translations."""
        # Fix for HTML fields
        for mname, fnames in self.model_translations.items():
            for fname, xml_ids in fnames.items():
                if not callable(self.env[mname]._fields[fname].translate):
                    continue
                for xml_id, langs in xml_ids.items():
                    src_value = self.env.ref(xml_id).with_context(lang="en_US")[fname]
                    src = str(src_value) if src_value else False
                    for lang, translation in langs.items():
                        # We should only use model_terms_translations if there is a
                        # value (src), otherwise the translation of this field will
                        # not be saved.
                        # If the data is empty in the database (null), the value will
                        # be defined directly.
                        if src:
                            self.model_terms_translations[mname][fname][xml_id][src][
                                lang
                            ] = translation
                        else:
                            self.env.ref(xml_id).with_context(lang=lang)[fname] = (
                                translation
                            )

        return super().save(overwrite=True, force_overwrite=True)


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
    update_tax_group = fields.Boolean(
        string="Update tax groups",
        default=True,
        help="Existing tax groups are updated. Tax group are searched by name.",
    )
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
    tax_group_ids = fields.One2many(
        comodel_name="wizard.update.charts.accounts.tax.group",
        inverse_name="update_chart_wizard_id",
        string="Taxe Groups",
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
    new_tax_groups = fields.Integer(compute="_compute_new_tax_group_count")
    new_taxes = fields.Integer(compute="_compute_new_taxes_count")
    new_accounts = fields.Integer(compute="_compute_new_accounts_count")
    new_account_groups = fields.Integer(compute="_compute_new_account_groups_count")
    rejected_new_account_number = fields.Integer()
    new_fps = fields.Integer(
        string="New fiscal positions", compute="_compute_new_fps_count"
    )
    updated_tax_groups = fields.Integer(compute="_compute_updated_tax_groups_count")
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
    tax_group_field_ids = fields.Many2many(
        comodel_name="ir.model.fields",
        relation="wizard_update_charts_tax_group_fields_rel",
        string="Tax group fields",
        domain=lambda self: self._domain_tax_group_field_ids(),
        default=lambda self: self._default_tax_group_field_ids(),
    )
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
    tax_group_matching_ids = fields.One2many(
        comodel_name="wizard.tax.group.matching",
        inverse_name="update_chart_wizard_id",
        string="Tax goups matching",
        default=lambda self: self._default_tax_group_matching_ids(),
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

    def _domain_tax_group_field_ids(self):
        return self._domain_per_name("account.tax.group") + [
            ("ttype", "!=", "one2many")
        ]

    def _domain_tax_field_ids(self):
        # Allow specific o2m fields critical for comparison
        # (repartition_line_ids) but exclude other o2m
        return self._domain_per_name("account.tax") + [
            "|",
            ("ttype", "!=", "one2many"),
            (
                "name",
                "in",
                [
                    "repartition_line_ids",
                ],
            ),
        ]

    def _domain_account_field_ids(self):
        return self._domain_per_name("account.account") + [("ttype", "!=", "one2many")]

    def _domain_account_group_field_ids(self):
        return self._domain_per_name("account.group") + [("ttype", "!=", "one2many")]

    def _domain_fp_field_ids(self):
        return self._domain_per_name("account.fiscal.position") + [
            "|",
            ("ttype", "!=", "one2many"),
            ("name", "in", ["account_ids"]),
        ]

    def _default_tax_group_field_ids(self):
        return [
            Command.link(x.id)
            for x in self.env["ir.model.fields"].search(
                self._domain_tax_group_field_ids()
                + self.get_uncheck_fields_domain("account.tax.group"),
            )
        ]

    def _default_tax_field_ids(self):
        return [
            Command.link(x.id)
            for x in self.env["ir.model.fields"].search(
                self._domain_tax_field_ids()
                + self.get_uncheck_fields_domain("account.tax"),
            )
        ]

    def _default_account_field_ids(self):
        return [
            Command.link(x.id)
            for x in self.env["ir.model.fields"].search(
                self._domain_account_field_ids()
                + self.get_uncheck_fields_domain("account.account"),
            )
        ]

    def _default_account_group_field_ids(self):
        return [
            Command.link(x.id)
            for x in self.env["ir.model.fields"].search(
                self._domain_account_group_field_ids()
                + self.get_uncheck_fields_domain("account.group")
            )
        ]

    def _default_fp_field_ids(self):
        return [
            Command.link(x.id)
            for x in self.env["ir.model.fields"].search(
                self._domain_fp_field_ids()
                + self.get_uncheck_fields_domain("account.fiscal.position")
            )
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

    def _default_tax_group_matching_ids(self):
        ordered_opts = ["xml_id", "name"]
        return self._get_matching_ids("wizard.tax.group.matching", ordered_opts)

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

    @api.depends("tax_group_ids")
    def _compute_new_tax_group_count(self):
        self.new_tax_groups = len(
            self.tax_group_ids.filtered(lambda x: x.type == "new")
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

    @api.depends("tax_group_ids")
    def _compute_updated_tax_groups_count(self):
        self.updated_tax_groups = len(
            self.tax_group_ids.filtered(lambda x: x.type == "updated")
        )

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
                "tax_group_ids": [Command.delete(r.id) for r in self.tax_group_ids],
                "tax_ids": [Command.delete(r.id) for r in self.tax_ids],
                "account_ids": [Command.delete(r.id) for r in self.account_ids],
                "fiscal_position_ids": [
                    Command.delete(r.id) for r in self.fiscal_position_ids
                ],
            }
        )
        return self._reopen()

    def _get_chart_template_data(self):
        chart_template_model = self.env["account.chart.template"]
        t_data = chart_template_model._get_chart_template_data(self.chart_template)
        model_mapping = {
            "account.group": self.update_account_group,
            "account.account": self.update_account,
            "account.tax.group": self.update_tax_group,
            "account.tax": self.update_tax,
            "account.fiscal.position": self.update_fiscal_position,
        }
        langs = self.env["res.lang"].search([("active", "=", True)])
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
                            # Only populate the per-language key when the
                            # template actually carries a translation for
                            # this language. Falling back to the English
                            # value here would cause diff_fields to compare
                            # the DB's real translation against the English
                            # source and incorrectly flag user-provided
                            # translations as drift.
                            if not field_translation:
                                continue
                            short_lang = lang.code.split("_")[0]
                            r_data[f"{f_name}@{short_lang}"] = field_translation
        return t_data

    def action_find_records(self):
        """Searchs for records to update/create and shows them."""
        self.env.registry.clear_cache()
        t_data = self._get_chart_template_data()
        # Search for, and load, the records to create/update.
        if self.update_account_group:
            self._find_account_groups(t_data["account.group"])
        if self.update_account:
            self._find_accounts(t_data["account.account"])
        if self.update_tax_group:
            self._find_tax_groups(t_data["account.tax.group"])
        if self.update_tax:
            self._find_taxes(t_data["account.tax"])
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
        if self.update_account_group:
            self._update_account_groups(t_data["account.group"])
        if self.update_account:
            self._update_accounts(t_data["account.account"])
        if self.update_tax_group:
            self._update_tax_groups(t_data["account.tax.group"])
        if self.update_fiscal_position:
            self._update_fiscal_positions(t_data["account.fiscal.position"])
        if self.update_tax:
            self._update_taxes(t_data["account.tax"])
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
        if isinstance(code, str):
            return code.ljust(self.code_digits, "0")
        _logger.info(
            "padded_code received a non-string value: %s. Returning it as is.", code
        )
        return code

    @api.model
    @tools.ormcache("name")
    def fields_to_ignore(self, name):
        """Get fields that will not be used when checking differences.

        :param str name: The name of the template model.
        :return set: Fields to ignore in diff.
        """
        mail_thread_fields = set(self.env["mail.thread"]._fields)
        specials_mapping = {
            "account.tax.group": mail_thread_fields | {"sequence", "tax_ids"},
            "account.tax": mail_thread_fields
            | {
                "children_tax_ids",
                "sequence",
            },
            "account.account": mail_thread_fields
            | {
                "root_id",
                "company_ids",
            },
            "account.group": {"parent_id"},
            "account.fiscal.position": {"tax_ids"},
        }
        specials = {
            "display_name",
            "__last_update",
            "company_id",
        } | specials_mapping.get(name, set())
        return set(models.MAGIC_COLUMNS) | specials

    @api.model
    def get_default_unchecked_fields(self, name):
        """Get fields that should be unchecked by default for a given model.

        :param str name: The name of the template model.
        :return set: Fields to uncheck by default.
        """
        unchecked_mapping = {
            "account.fiscal.position": {"sequence"},
        }
        return unchecked_mapping.get(name, set())

    def get_uncheck_fields_domain(self, name):
        unchecked_fields = list(self.get_default_unchecked_fields(name))
        return [("name", "not in", unchecked_fields)]

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
        langs = self.env["res.lang"].search([("active", "=", True)])
        # If the fields to be queried are not mapped, use all of them
        # (example: account.tax.repartition.line).
        if real._name not in field_mapping:
            field_mapping[real._name] = self.env["ir.model.fields"].search(
                self._domain_per_name(real._name)
            )
        fields_by_key = {x.name: x for x in field_mapping[real._name]}
        to_include = field_mapping[real._name].mapped("name")
        for key in record_values.keys():
            if key in ignore or key not in to_include:
                continue
            field_info = fields_by_key.get(key)
            # Skip empty scalar templates so unset fields aren't flagged,
            # but let empty m2m/o2m/boolean values through so that an
            # explicit "clear links" in the template is detected when the
            # real record has values.
            if (
                field_info
                and field_info.ttype not in ("boolean", "many2many", "one2many")
                and not record_values.get(key)
            ):
                continue
            field = fields_by_key[key]
            record_value, real_value = record_values[key], real[key]
            if real._name == "account.account" and key == "code":
                record_value = self.padded_code(record_value)
                real_value = self.padded_code(real_value)
            # Field ttype conditions
            if field.ttype == "many2many":
                # Normalize falsy template values (None/False/"") so an
                # explicit "no links" is compared like an empty string.
                record_value = record_value or ""
                if isinstance(record_value, str):
                    # If any template xmlid can't be resolved we skip the
                    # check — we can't reliably tell whether the link is
                    # drifted or just pointing to a record whose xmlid was
                    # unlinked (tracked separately by `missing_xml_id`).
                    expected_ids = set()
                    unresolved = False
                    for v in filter(None, record_value.split(",")):
                        xml_id = (
                            f"account.{self.company_id.id}_{v}" if "." not in v else v
                        )
                        rec = self.env.ref(xml_id, raise_if_not_found=False)
                        if rec:
                            expected_ids.add(rec.id)
                        else:
                            unresolved = True
                    if not unresolved and set(real_value.ids) != expected_ids:
                        result[key] = record_value
                else:
                    # record_value is an ORM command list. Collect the
                    # expected record ids from SET (6) and LINK (4)
                    # commands and compare as an unordered set.
                    expected_cmd_ids = set()
                    for cmd in (
                        c for c in record_value if isinstance(c, list | tuple) and c
                    ):
                        if cmd[0] == 6 and len(cmd) >= 3 and isinstance(cmd[2], list):
                            expected_cmd_ids = set(cmd[2])
                        elif cmd[0] == 4:
                            expected_cmd_ids.add(cmd[1])
                    if expected_cmd_ids != set(real_value.ids):
                        result[key] = record_value
                continue
            elif field.ttype == "many2one":
                if isinstance(record_value, int):
                    if record_value != real_value.id:
                        result[key] = record_value
                    continue
                real_xml_id = self._get_external_id(real_value) if real_value else False
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
                en_value = (real.with_context(lang="en_US")[key] or "").strip()
                if field.ttype == "html":
                    en_value = tools.mail.html_to_inner_content(en_value)
                for lang in langs:
                    if lang.code == "en_US":
                        key_lang = key
                    else:
                        short_lang = lang.code.split("_")[0]
                        key_lang = f"{key}@{short_lang}"
                    if key_lang not in record_values:
                        continue
                    real_value_lang = (
                        real.with_context(lang=lang.code)[key] or ""
                    ).strip()
                    record_value_lang = record_values[key_lang].strip()
                    if field.ttype == "html":
                        # Convert HTML to inner content for comparison
                        # especially to prevent comparing str with Markup
                        real_value_lang = tools.mail.html_to_inner_content(
                            real_value_lang
                        )
                    # Skip non-English variants whose actual value is just
                    # the English fallback: there's no stored translation
                    # for that language, so the diff would only reflect
                    # Odoo's read-time fallback, not real drift.
                    if lang.code != "en_US" and real_value_lang == en_value:
                        continue
                    if record_value_lang != real_value_lang:
                        result[key_lang] = record_value_lang
            elif field.ttype == "html":
                # Convert HTML to inner content for comparison
                # especially to prevent comparing str with Markup
                real_value = tools.mail.html_to_inner_content(real_value)
                if record_value != real_value:
                    result[key] = record_value
            elif record_value != real_value:
                result[key] = record_value
        # The template CSV loader drops empty cells from record_values (see
        # account.chart.template._parse_csv), so an explicit "no tags"
        # column never reaches us. For tracked m2m/o2m fields that are
        # absent from the template data, flag drift if the real record
        # still has links — that's the only way the wizard can report
        # e.g. an account whose template has tag_ids="" but whose DB
        # record carries tags.
        for key, field in fields_by_key.items():
            if (
                key in ignore
                or key in result
                or key in record_values
                or field.ttype not in ("many2many", "one2many", "boolean")
            ):
                continue
            # Skip readonly/inverse fields — they're populated automatically
            # (e.g. `replacing_tax_ids`) and can't be overwritten anyway.
            orm_field = real._fields.get(key)
            if not orm_field or orm_field.readonly:
                continue
            if field.ttype == "boolean":
                # If the Boolean field is computed, create a new pseudo-record
                # and compute its value
                if getattr(orm_field, "compute", None):
                    expected_record = real.new(real.read()[0])
                    getattr(expected_record, orm_field.compute)()
                    expected = expected_record[key]
                else:
                    expected = real.default_get([key]).get(key, False)
                if bool(real[key]) != bool(expected):
                    result[key] = expected
            elif real[key]:
                result[key] = ""
        # __translation_module__
        if len(result.keys()) > 0 and not self.env.context.get("skip_translation_keys"):
            if "__translation_module__" in record_values:
                result["__translation_module__"] = record_values[
                    "__translation_module__"
                ]
        return result

    @api.model
    def diff_notes(self, record_values, real):
        """Get notes for humans on why this record is going to be updated.

        Shows each differing field with a concise "actual → expected" detail
        so the user can audit the proposed change before accepting it.
        """
        diff = self.with_context(skip_translation_keys=True).diff_fields(
            record_values, real
        )
        # Collapse translation variants (e.g. name@fr) onto their base field.
        by_field = {}
        for key in diff:
            base = key.split("@", 1)[0] if "@" in key else key
            by_field.setdefault(base, []).append(key)
        if not by_field:
            return ""
        # Merge the diff result on top of record_values so synthesized
        # drift (e.g. booleans absent from the template but expected to
        # match the field's default) renders its real expected value
        # instead of `bool(None) = False`.
        effective_values = {**record_values, **diff}
        lines = [self.env._("Differences in these fields:")]
        for base in sorted(
            by_field, key=lambda n: real._fields[n].get_description(self.env)["string"]
        ):
            field = real._fields[base]
            label = field.get_description(self.env)["string"]
            detail = self._diff_note_detail(
                field, real, effective_values, by_field[base]
            )
            lines.append(f"- {label}: {detail}" if detail else f"- {label}")
        return "\n".join(lines)

    @staticmethod
    def _diff_note_truncate(value):
        text = "" if value is None or value is False else str(value)
        return text if len(text) <= 80 else text[:77] + "…"

    def _diff_note_resolve_xmlid(self, short_or_full):
        xml_id = (
            f"account.{self.company_id.id}_{short_or_full}"
            if "." not in short_or_full
            else short_or_full
        )
        return self.env.ref(xml_id, raise_if_not_found=False)

    @staticmethod
    def _diff_note_label(rec):
        """Fallback label for sub-records whose `display_name` is the parent."""
        if rec._name == "account.fiscal.position.account":
            return (
                f"{rec.account_src_id.display_name} "
                f"→ {rec.account_dest_id.display_name}"
            )
        if rec._name == "account.tax.repartition.line":
            return f"{rec.document_type}/{rec.repartition_type} {rec.factor_percent:g}%"
        return rec.display_name

    def _diff_note_expected_m2x_names(self, expected_v, comodel_name):
        """Resolve an m2m/o2m template value (xmlid string or command list)
        to a sorted list of display names."""
        names = []
        if isinstance(expected_v, str):
            for v in filter(None, expected_v.split(",")):
                rec = self._diff_note_resolve_xmlid(v)
                names.append(rec.display_name if rec else v)
        elif isinstance(expected_v, list | tuple) and comodel_name:
            Comodel = self.env[comodel_name]
            for cmd in (
                c for c in expected_v if isinstance(c, list | tuple) and len(c) >= 3
            ):
                if cmd[0] == 6 and isinstance(cmd[2], list):
                    names = Comodel.browse(cmd[2]).mapped("display_name")
                    break
                if cmd[0] == 4:
                    names.append(Comodel.browse(cmd[1]).display_name)
        return sorted(names)

    def _diff_note_sub_detail(self, sub_vals, rec, diff_keys):
        """Render "field actual → expected" parts for a single sub-record."""
        parts = []
        for k in diff_keys:
            sub_field = rec._fields.get(k)
            actual_v = rec[k] if sub_field else None
            expected_v = sub_vals.get(k)
            ttype = sub_field.type if sub_field else None
            if ttype == "many2one":
                a_name = actual_v.display_name if actual_v else ""
                e_rec = (
                    self._diff_note_resolve_xmlid(expected_v)
                    if isinstance(expected_v, str)
                    else None
                )
                e_name = e_rec.display_name if e_rec else (expected_v or "")
                parts.append(f"{k} '{a_name}' → '{e_name}'")
            elif ttype in ("many2many", "one2many"):
                a_names = sorted(actual_v.mapped("display_name")) if actual_v else []
                e_names = self._diff_note_expected_m2x_names(
                    expected_v, sub_field.comodel_name
                )
                a_str = ", ".join(a_names) or "∅"
                e_str = ", ".join(e_names) or "∅"
                parts.append(
                    f"{k} [{self._diff_note_truncate(a_str)}]"
                    f" → [{self._diff_note_truncate(e_str)}]"
                )
            else:
                parts.append(
                    f"{k} '{self._diff_note_truncate(actual_v)}'"
                    f" → '{self._diff_note_truncate(expected_v)}'"
                )
        return "; ".join(parts)

    def _diff_note_commands(self, field, actual, expected_raw):
        """Detail string for an m2m/o2m whose template value is a command list."""
        actual_count = len(actual)
        expected_count = 0
        for cmd in (c for c in expected_raw if isinstance(c, list | tuple) and c):
            if cmd[0] in (0, 4):  # CREATE / LINK
                expected_count += 1
            elif cmd[0] == 6 and len(cmd) >= 3:  # SET
                expected_count += len(cmd[2])
        if actual_count != expected_count:
            return self.env._(
                "%(actual)s record(s) → %(expected)s record(s)",
                actual=actual_count,
                expected=expected_count,
            )
        sub_diffs = []
        for idx, cmd in (
            (i, c)
            for i, c in enumerate(expected_raw[:actual_count])
            if isinstance(c, list | tuple) and len(c) >= 3 and isinstance(c[2], dict)
        ):
            sub_diff = self.with_context(skip_translation_keys=True).diff_fields(
                cmd[2], actual[idx]
            )
            diff_keys = sorted(k for k in sub_diff if k != "__translation_module__")
            if diff_keys:
                detail = self._diff_note_sub_detail(cmd[2], actual[idx], diff_keys)
                sub_diffs.append(f"#{idx + 1}: {detail}")
            if len(sub_diffs) >= 3:
                break
        if sub_diffs:
            return "\n    " + "\n    ".join(sub_diffs)
        return self.env._(
            "%(n)s record(s) → differs from template",
            n=actual_count,
        )

    def _diff_note_m2x(self, field, actual, expected_raw):
        """Detail string for an m2m/o2m field."""
        actual_names = (
            sorted(self._diff_note_label(rec) for rec in actual) if actual else []
        )
        if isinstance(expected_raw, str) or not expected_raw:
            expected_names = self._diff_note_expected_m2x_names(
                expected_raw, field.comodel_name
            )
            actual_str = ", ".join(actual_names) or "∅"
            expected_str = ", ".join(expected_names) or "∅"
            return (
                f"[{self._diff_note_truncate(actual_str)}]"
                f" → [{self._diff_note_truncate(expected_str)}]"
            )
        return self._diff_note_commands(field, actual, expected_raw)

    def _diff_note_m2o(self, field, actual, expected_raw):
        """Detail string for a many2one field."""
        actual_name = actual.display_name if actual else ""
        expected_name = ""
        if isinstance(expected_raw, str):
            rec = self._diff_note_resolve_xmlid(expected_raw)
            expected_name = rec.display_name if rec else expected_raw
        elif isinstance(expected_raw, int):
            rec = self.env[field.comodel_name].browse(expected_raw)
            expected_name = rec.display_name if rec.exists() else str(expected_raw)
        return (
            f"'{self._diff_note_truncate(actual_name)}'"
            f" → '{self._diff_note_truncate(expected_name)}'"
        )

    def _diff_note_detail(self, field, real, record_values, diff_keys=None):
        """Return a "actual → expected" string for a differing field.

        `diff_keys` lists the actual keys from the diff for this field (e.g.
        ["name", "name@fr"]); for translatable fields we use it to render
        per-language details so the bullet always reads the same-language
        actual value rather than whatever `env.lang` happened to be.
        """
        if field.translate and diff_keys:
            return self._diff_note_translation_detail(
                field, real, record_values, diff_keys
            )
        actual = real[field.name]
        expected_raw = record_values.get(field.name)
        if field.type in ("many2many", "one2many"):
            return self._diff_note_m2x(field, actual, expected_raw)
        if field.type == "many2one":
            return self._diff_note_m2o(field, actual, expected_raw)
        if field.type == "boolean":
            return f"{bool(actual)} → {bool(expected_raw)}"
        return (
            f"'{self._diff_note_truncate(actual)}'"
            f" → '{self._diff_note_truncate(expected_raw)}'"
        )

    def _diff_note_translation_detail(self, field, real, record_values, diff_keys):
        """Render per-language details for a translatable field whose diff
        includes translation variants (e.g. `name@fr`).

        Variants are only present in ``diff_keys`` when ``diff_fields``
        decided the per-language value really drifted, so we can render
        them directly without re-checking against the English fallback.
        """
        active_langs = self.env["res.lang"].search([("active", "=", True)])
        by_short = {}
        for lang in active_langs:
            by_short.setdefault(lang.code.split("_")[0], lang)
        parts = []
        for key in sorted(diff_keys):
            if "@" in key:
                short = key.split("@", 1)[1]
                lang = by_short.get(short)
                lang_code = lang.code if lang else "en_US"
                lang_label = short
            else:
                lang_code = "en_US"
                lang_label = "en"
            actual = real.with_context(lang=lang_code)[field.name] or ""
            expected = record_values.get(key) or ""
            if field.type == "html":
                actual = tools.mail.html_to_inner_content(actual) if actual else ""
                expected = (
                    tools.mail.html_to_inner_content(expected) if expected else ""
                )
            parts.append(
                f"[{lang_label}] '{self._diff_note_truncate(actual)}'"
                f" → '{self._diff_note_truncate(expected)}'"
            )
        return "; ".join(parts)

    def _domain_taxes_to_deactivate(self, found_taxes_ids):
        return [
            ("company_id", "=", self.company_id.id),
            ("id", "not in", found_taxes_ids),
            ("active", "=", True),
        ]

    def _find_record_matching(self, model_name, xmlid, data):
        mapped_fields = {
            "account.group": self.account_group_matching_ids,
            "account.account": self.account_matching_ids,
            "account.tax.group": self.tax_group_matching_ids,
            "account.tax": self.tax_matching_ids,
            "account.fiscal.position": self.fp_matching_ids,
        }
        company = self.company_id
        model = self.env[model_name]
        company_domain = []
        if "company_id" in model._fields:
            company_domain = [("company_id", "=", company.id)]
        elif "company_ids" in model._fields:
            company_domain = [("company_ids", "in", company.ids)]
        for matching in mapped_fields[model_name].sorted("sequence"):
            if matching.matching_value == "xml_id":
                full_xmlid = (
                    f"account.{company.id}_{xmlid}" if "." not in xmlid else xmlid
                )
                record = self.env.ref(full_xmlid, raise_if_not_found=False)
                if record:
                    # To read company-dependent fields correctly
                    return record.with_company(company)
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
        external_ids = record.get_external_id()
        return external_ids.get(record.id, False)

    def missing_xml_id(self, record, xml_id):
        record_xml_ids = record._get_external_ids()[record.id]
        full_xml_id = (
            f"account.{self.company_id.id}_{xml_id}" if "." not in xml_id else xml_id
        )
        return full_xml_id not in record_xml_ids

    def _missing_xml_id_note(self, record, xml_id):
        """Human-readable note for a missing xml_id, showing expected vs
        the ones currently attached to the record."""
        full = f"account.{self.company_id.id}_{xml_id}" if "." not in xml_id else xml_id
        current = record._get_external_ids().get(record.id, [])
        current_str = ", ".join(current) or self.env._("none")
        return self.env._(
            "Missing XML-ID (expected %(expected)s; currently: %(current)s).",
            expected=full,
            current=current_str,
        )

    def recreate_xml_id(self, record, xml_id):
        """Recreate the xml_id if it is different than expected, otherwise
        chart.template won't do it correctly.
        """
        if not self.missing_xml_id(record, xml_id):
            return
        try:
            module, name = xml_id.split(".")
        except ValueError:
            module = "account"
            name = f"{self.company_id.id}_{xml_id}"
        self.env["ir.model.data"].create(
            {
                "module": module,
                "model": record._name,
                "name": name,
                "res_id": record.id,
                "noupdate": True,
            }
        )

    def _find_tax_groups(self, t_data):
        """Search for, and load, template data to create/update/delete."""
        found_tax_groups_ids = []
        tax_group_vals = []
        for xmlid, r_data in t_data.items():
            tax_group = self._find_record_matching("account.tax.group", xmlid, r_data)
            # Check if the template data matches a real tax group
            if not tax_group:
                # Tax group to be created
                tax_group_vals.append(
                    {
                        "xml_id": xmlid,
                        "update_chart_wizard_id": self.id,
                        "type": "new",
                        "notes": self.env._("Name or description not found."),
                    }
                )
            else:
                found_tax_groups_ids.append(tax_group.id)
                # Check the tax group for changes
                notes = self.diff_notes(r_data, tax_group)
                if self.missing_xml_id(tax_group, xmlid):
                    notes += (notes and "\n" or "") + self._missing_xml_id_note(
                        tax_group, xmlid
                    )
                if notes:
                    # Tax group to be updated
                    tax_group_vals.append(
                        {
                            "xml_id": xmlid,
                            "update_chart_wizard_id": self.id,
                            "type": "updated",
                            "update_tax_group_id": tax_group.id,
                            "notes": notes,
                        }
                    )
        self.tax_group_ids = [Command.clear()] + [
            Command.create(tax_group_val) for tax_group_val in tax_group_vals
        ]

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
                        "notes": self.env._("Name or description not found."),
                    }
                )
            else:
                found_taxes_ids.append(tax.id)
                # Check the tax for changes
                notes = self.diff_notes(r_data, tax)
                if self.missing_xml_id(tax, xmlid):
                    notes += (notes and "\n" or "") + self._missing_xml_id_note(
                        tax, xmlid
                    )
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
                    "notes": self.env._("To deactivate: not in the template"),
                }
            )
        self.tax_ids = [Command.clear()] + [
            Command.create(tax_val) for tax_val in tax_vals
        ]

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
                        "notes": self.env._("No account found with this code."),
                    }
                )
            else:
                # Check the account for changes
                notes = self.diff_notes(r_data, account)
                if self.missing_xml_id(account, xmlid):
                    notes += (notes and "\n" or "") + self._missing_xml_id_note(
                        account, xmlid
                    )
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
        self.account_ids = [Command.clear()] + [
            Command.create(a_val) for a_val in account_vals
        ]

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
                        "notes": self.env._("No account found with this code."),
                    }
                )
            else:
                # Check the account for changes
                notes = self.diff_notes(r_data, account_group)
                code_prefix_end = (
                    r_data["code_prefix_end"]
                    if r_data.get("code_prefix_end")
                    and r_data["code_prefix_end"] >= r_data["code_prefix_start"]
                    else r_data["code_prefix_start"]
                )
                if code_prefix_end != account_group.code_prefix_end:
                    label = account_group._fields["code_prefix_end"].get_description(
                        self.env
                    )["string"]
                    line = self.env._(
                        "- %(label)s: '%(actual)s' → '%(expected)s'",
                        label=label,
                        actual=account_group.code_prefix_end or "",
                        expected=code_prefix_end or "",
                    )
                    if notes:
                        # Append under the existing "Differences in these fields:"
                        # header produced by diff_notes.
                        notes += f"\n{line}"
                    else:
                        notes = self.env._("Differences in these fields:") + f"\n{line}"
                if self.missing_xml_id(account_group, xmlid):
                    notes += (notes and "\n" or "") + self._missing_xml_id_note(
                        account_group, xmlid
                    )
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
        self.account_group_ids = [Command.clear()] + [
            Command.create(ag_val) for ag_val in ag_vals
        ]

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
                        "notes": self.env._("No fiscal position found with this name."),
                    }
                )
            else:
                # Check the fiscal position for changes
                notes = self.diff_notes(r_data, fp)
                if self.missing_xml_id(fp, xmlid):
                    notes += (notes and "\n" or "") + self._missing_xml_id_note(
                        fp, xmlid
                    )
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
        self.fiscal_position_ids = [Command.clear()] + [
            Command.create(fp_val) for fp_val in fp_vals
        ]

    def _load_data(self, model, data):
        """Process similar to the one in chart template _load() method."""
        template = self.env["account.chart.template"].with_context(
            default_company_id=self.company_id.id,
            allowed_company_ids=[self.company_id.id],
            tracking_disable=True,
            delay_account_group_sync=True,
            lang="en_US",
        )
        model_fields = set(self.env[model]._fields)
        filtered_data = {
            xml_id: {
                k: v
                for k, v in vals.items()
                if k in model_fields or "@" in k or k == "__translation_module__"
            }
            for xml_id, vals in data.items()
        }
        created_records = template._load_data({model: filtered_data})[model]
        # Make sure all translation data is indexed by XML ID
        translation_data = {}
        created_xmlids = created_records.get_external_id()
        for _id, record_data in data.items():
            xml_id = _id
            if isinstance(_id, int):
                xml_id = created_xmlids.get(xml_id)
            if not xml_id:
                continue
            translation_data[xml_id] = record_data
        with patch(
            "odoo.addons.account.models.chart_template.TranslationImporter",
            _OverwritingTranslationImporter,
        ):
            template._load_translations(
                companies=self.company_id, template_data={model: translation_data}
            )
        created_records.invalidate_recordset()
        for record in created_records:
            msg = self.env._(
                (f"Created/updated {record._name} %s."),
                f"'{record.name}' (ID:{record.id})",
            )
            _logger.info(msg)
            if not self.log:
                self.log = msg
            else:
                self.log += f"\n{msg}"

    def _update_tax_groups(self, t_data):
        """Process account groups templates to create/update."""
        data = {}
        for wiz_tg in self.tax_group_ids:
            tg = wiz_tg.update_tax_group_id
            xml_id = wiz_tg.xml_id
            key = tg.id or xml_id
            t_data_item = t_data[xml_id]
            data_item = t_data_item if wiz_tg.type == "new" else {}
            if wiz_tg.type == "updated":
                self.recreate_xml_id(tg, xml_id)
                data_item = self.diff_fields(t_data_item, tg)
            data[key] = data_item
        self._load_data("account.tax.group", data)

    def _update_taxes(self, t_data):
        """Process taxes to create/update/deactivate."""
        # First create taxes in batch
        data = {}
        for wiz_tax in self.tax_ids:
            tax = wiz_tax.update_tax_id
            if wiz_tax.type == "deleted":
                tax.active = False
                _logger.info(self.env._("Deactivated tax %s."), tax.name)
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
            else:
                data_item["code"] = self.padded_code(data_item["code"])
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


class WizardUpdateChartsAccountsTaxGroup(models.TransientModel):
    _name = "wizard.update.charts.accounts.tax.group"
    _description = (
        "Tax group that needs to be updated (new or updated in the template)."
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
            ("new", "New tax group"),
            ("updated", "Updated tax group"),
        ],
        readonly=False,
    )
    update_tax_group_id = fields.Many2one(
        comodel_name="account.tax.group",
        string="Tax group to update",
        required=False,
        ondelete="set null",
    )
    notes = fields.Text(readonly=True)


class WizardUpdateChartsAccountsTax(models.TransientModel):
    _name = "wizard.update.charts.accounts.tax"
    _description = "Tax that needs to be updated (new or updated in the template)."

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
    _description = "Account that needs to be updated (new or updated in the template)."

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
        "Fiscal position that needs to be updated (new or updated in the template)."
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


class WizardTaxGroupMatching(models.TransientModel):
    _name = "wizard.tax.group.matching"
    _description = "Wizard Tax Group Matching"
    _inherit = "wizard.matching"

    def _get_matching_selection(self):
        vals = super()._get_matching_selection()
        vals += self._selection_from_files("account.tax.group", ["name"])
        return vals


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
