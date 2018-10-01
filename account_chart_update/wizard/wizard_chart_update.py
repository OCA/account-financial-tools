# -*- coding: utf-8 -*-
# © 2010 Jordi Esteve, Zikzakmedia S.L. (http://www.zikzakmedia.com)
# © 2010 Pexego Sistemas Informáticos S.L.(http://www.pexego.es)
#        Borja López Soilán
# © 2013 Joaquin Gutierrez (http://www.gutierrezweb.es)
# © 2015 Antonio Espinosa <antonioea@tecnativa.com>
# © 2016 Jairo Llopis <jairo.llopis@tecnativa.com>
# © 2016 Jacques-Etienne Baudoux <je@bcim.be>
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, exceptions, fields, models, tools
from odoo.tools import config
from contextlib import closing
from cStringIO import StringIO
import logging

_logger = logging.getLogger(__name__)
EXCEPTION_TEXT = u"Traceback (most recent call last)"


class WizardUpdateChartsAccounts(models.TransientModel):
    _name = 'wizard.update.charts.accounts'

    state = fields.Selection(
        selection=[('init', 'Configuration'),
                   ('ready', 'Select records to update'),
                   ('done', 'Wizard completed')],
        string='Status', readonly=True, default='init')
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company', required=True,
        ondelete='set null', default=lambda self: self.env.user.company_id.id)
    chart_template_id = fields.Many2one(
        comodel_name='account.chart.template', string='Chart Template',
        ondelete='cascade', required=True)
    chart_template_ids = fields.Many2many(
        "account.chart.template",
        string="Chart Templates",
        compute="_compute_chart_template_ids",
        help="Includes all chart templates.")
    code_digits = fields.Integer(
        string='# of digits', required=True,
        help="No. of digits to use for account code. "
             "Make sure it is the same number as existing accounts.")
    lang = fields.Selection(
        lambda self: self._get_lang_selection_options(), 'Language', size=5,
        required=True,
        help="For records searched by name (taxes, fiscal "
             "positions), the template name will be matched against the "
             "record name on this language.",
        default=lambda self: self.env.context.get('lang', self.env.user.lang))
    update_tax = fields.Boolean(
        string='Update taxes', default=True,
        help="Existing taxes are updated. Taxes are searched by name.")
    update_account = fields.Boolean(
        string='Update accounts', default=True,
        help="Existing accounts are updated. Accounts are searched by code.")
    update_fiscal_position = fields.Boolean(
        string='Update fiscal positions', default=True,
        help="Existing fiscal positions are updated. Fiscal positions are "
             "searched by name.")
    continue_on_errors = fields.Boolean(
        string="Continue on errors", default=False,
        help="If set, the wizard will continue to the next step even if "
             "there are minor errors.")
    tax_ids = fields.One2many(
        comodel_name='wizard.update.charts.accounts.tax', ondelete='cascade',
        inverse_name='update_chart_wizard_id', string='Taxes')
    account_ids = fields.One2many(
        comodel_name='wizard.update.charts.accounts.account',
        inverse_name='update_chart_wizard_id', string='Accounts',
        ondelete='cascade')
    fiscal_position_ids = fields.One2many(
        comodel_name='wizard.update.charts.accounts.fiscal.position',
        inverse_name='update_chart_wizard_id', string='Fiscal positions',
        ondelete='cascade')
    new_taxes = fields.Integer(
        string='New taxes', compute="_compute_new_taxes_count")
    new_accounts = fields.Integer(
        string='New accounts',
        compute="_compute_new_accounts_count")
    rejected_new_account_number = fields.Integer()
    new_fps = fields.Integer(
        string='New fiscal positions',
        compute="_compute_new_fps_count")
    updated_taxes = fields.Integer(
        string='Updated taxes',
        compute="_compute_updated_taxes_count")
    rejected_updated_account_number = fields.Integer()
    updated_accounts = fields.Integer(
        string='Updated accounts',
        compute="_compute_updated_accounts_count")
    updated_fps = fields.Integer(
        string='Updated fiscal positions',
        compute="_compute_updated_fps_count")
    deleted_taxes = fields.Integer(
        string='Deactivated taxes',
        compute="_compute_deleted_taxes_count")
    log = fields.Text(string='Messages and Errors', readonly=True)

    @api.model
    def _get_lang_selection_options(self):
        """Gets the available languages for the selection."""
        langs = self.env['res.lang'].search([])
        return [(lang.code, lang.name) for lang in langs]

    @api.multi
    @api.depends("chart_template_id")
    def _compute_chart_template_ids(self):
        self.chart_template_ids = (
            self.env['wizard.multi.charts.accounts']
            ._get_chart_parent_ids(self.chart_template_id))

    @api.multi
    @api.depends('tax_ids')
    def _compute_new_taxes_count(self):
        self.new_taxes = len(self.tax_ids.filtered(lambda x: x.type == 'new'))

    @api.multi
    @api.depends('account_ids')
    def _compute_new_accounts_count(self):
        self.new_accounts = len(
            self.account_ids.filtered(lambda x: x.type == 'new')
        ) - self.rejected_new_account_number

    @api.multi
    @api.depends('fiscal_position_ids')
    def _compute_new_fps_count(self):
        self.new_fps = len(
            self.fiscal_position_ids.filtered(lambda x: x.type == 'new'))

    @api.multi
    @api.depends('tax_ids')
    def _compute_updated_taxes_count(self):
        self.updated_taxes = len(
            self.tax_ids.filtered(lambda x: x.type == 'updated'))

    @api.multi
    @api.depends('account_ids')
    def _compute_updated_accounts_count(self):
        self.updated_accounts = len(
            self.account_ids.filtered(lambda x: x.type == 'updated')
        ) - self.rejected_updated_account_number

    @api.multi
    @api.depends('fiscal_position_ids')
    def _compute_updated_fps_count(self):
        self.updated_fps = len(
            self.fiscal_position_ids.filtered(lambda x: x.type == 'updated'))

    @api.multi
    @api.depends('tax_ids')
    def _compute_deleted_taxes_count(self):
        self.deleted_taxes = len(
            self.tax_ids.filtered(lambda x: x.type == 'deleted'))

    @api.multi
    @api.onchange("company_id")
    def _onchage_company_update_chart_template(self):
        self.chart_template_id = self.company_id.chart_template_id

    @api.model
    def _get_code_digits(self, company=None):
        """Returns the number of digits for the accounts, fetched from
        the company.
        """
        if company is None:
            company = self.env.user.company_id
        return company.accounts_code_digits or 6

    @api.onchange('company_id')
    def onchange_company_id(self):
        """Update the code digits when the company changes"""
        self.code_digits = self._get_code_digits(company=self.company_id)

    @api.multi
    def _reopen(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'res_model': self._name,
            'target': 'new',
            # save original model in context,
            # because selecting the list of available
            # templates requires a model in context
            'context': {
                'default_model': self._name,
            },
        }

    @api.multi
    def action_init(self):
        """Initial action that sets the initial state."""
        self.state = 'init'
        return self._reopen()

    @api.multi
    def action_find_records(self):
        """Searchs for records to update/create and shows them."""
        self = self.with_context(lang=self.lang)
        # Search for, and load, the records to create/update.
        if self.update_tax:
            self._find_taxes()
        if self.update_account:
            self._find_accounts()
        if self.update_fiscal_position:
            self._find_fiscal_positions()
        # Write the results, and go to the next step.
        self.state = 'ready'
        return self._reopen()

    @api.multi
    def action_update_records(self):
        """Action that creates/updates/deletes the selected elements."""
        self = self.with_context(lang=self.lang)
        self.rejected_new_account_number = 0
        self.rejected_updated_account_number = 0
        with closing(StringIO()) as log_output:
            handler = logging.StreamHandler(log_output)
            _logger.addHandler(handler)
            # Create or update the records.
            if self.update_tax:
                self._update_taxes()
            perform_rest = True
            if self.update_account:
                self._update_accounts()
                if (EXCEPTION_TEXT in log_output.getvalue().decode('utf-8') and
                        not self.continue_on_errors):  # Abort early
                    perform_rest = False
            # Clear this cache for avoiding incorrect account hits (as it was
            # queried before account creation)
            self.find_account_by_templates.clear_cache(self)
            if self.update_tax and perform_rest:
                self._update_taxes_pending_for_accounts()
            if self.update_fiscal_position and perform_rest:
                self._update_fiscal_positions()
            # Store new chart in the company
            self.company_id.chart_template_id = self.chart_template_id
            _logger.removeHandler(handler)
            self.log = log_output.getvalue()
        # Check if errors where detected and wether we should stop.
        if EXCEPTION_TEXT in self.log and not self.continue_on_errors:
            raise exceptions.Warning(
                _("One or more errors detected!\n\n%s") % self.log)
        # Store the data and go to the next step.
        self.state = 'done'
        return self._reopen()

    @api.multi
    @tools.ormcache("templates")
    def find_tax_by_templates(self, templates):
        """Find a tax that matches the template."""
        # search inactive taxes too, to avoid re-creating
        # taxes that have been deactivated before
        Tax = self.env['account.tax'].with_context(active_test=False)
        result = Tax
        for template in templates:
            single = Tax
            criteria = (
                ("name", "=", template.name),
                ("description", "=", template.name),
                ("name", "=", template.description),
                ("description", "=", template.description),
            )
            for domain in criteria:
                if single:
                    break
                if domain[2]:
                    single = Tax.search(
                        [domain,
                         ("company_id", "=", self.company_id.id),
                         ("type_tax_use", "=", template.type_tax_use)],
                        limit=1)
            result |= single
        return result[:1].id

    @api.model
    @tools.ormcache("code")
    def padded_code(self, code):
        """Return a right-zero-padded code with the chosen digits."""
        return code.ljust(self.code_digits, '0')

    @api.multi
    @tools.ormcache("templates")
    def find_account_by_templates(self, templates):
        """Find an account that matches the template."""
        return self.env['account.account'].search(
            [('code', 'in', map(self.padded_code, templates.mapped("code"))),
             ('company_id', '=', self.company_id.id)],
        ).id

    @api.multi
    @tools.ormcache("templates")
    def find_fp_by_templates(self, templates):
        """Find a real fiscal position from a template."""
        return self.env['account.fiscal.position'].search(
            [('name', 'in', templates.mapped("name")),
             ('company_id', '=', self.company_id.id)], limit=1).id

    @api.multi
    @tools.ormcache("templates", "current_fp_accounts")
    def find_fp_account_by_templates(self, templates, current_fp_accounts):
        result = []
        for tpl in templates:
            pos_id = self.find_fp_by_templates(tpl.position_id)
            src_id = self.find_account_by_templates(tpl.account_src_id)
            dest_id = self.find_account_by_templates(tpl.account_dest_id)
            existing = self.env["account.fiscal.position.account"].search([
                ("position_id", "=", pos_id),
                ("account_src_id", "=", src_id),
                ("account_dest_id", "=", dest_id),
            ])
            if not existing:
                # create a new mapping
                result.append((0, 0, {
                    'position_id': pos_id,
                    'account_src_id': src_id,
                    'account_dest_id': dest_id,
                }))
            else:
                current_fp_accounts -= existing
        # Mark to be removed the lines not found
        if current_fp_accounts:
            result += [(2, x.id) for x in current_fp_accounts]
        return result

    @api.multi
    @tools.ormcache("templates", "current_fp_taxes")
    def find_fp_tax_by_templates(self, templates, current_fp_taxes):
        result = []
        for tpl in templates:
            pos_id = self.find_fp_by_templates(tpl.position_id)
            src_id = self.find_tax_by_templates(tpl.tax_src_id)
            dest_id = self.find_tax_by_templates(tpl.tax_dest_id)
            existing = self.env["account.fiscal.position.tax"].search([
                ("position_id", "=", pos_id),
                ("tax_src_id", "=", src_id),
                ("tax_dest_id", "=", dest_id),
            ])
            if not existing:
                # create a new mapping
                result.append((0, 0, {
                    'position_id': pos_id,
                    'tax_src_id': src_id,
                    'tax_dest_id': dest_id,
                }))
            else:
                current_fp_taxes -= existing
        # Mark to be removed the lines not found
        if current_fp_taxes:
            result += [(2, x.id) for x in current_fp_taxes]
        return result

    @api.model
    @tools.ormcache("name")
    def fields_to_ignore(self, template, name):
        """Get fields that will not be used when checking differences.

        :param str template: A template record.
        :param str name: The name of the template model.
        :return set: Fields to ignore in diff.
        """
        specials_mapping = {
            "account.tax.template": {
                "children_tax_ids",
            },
            "account.account.template": {
                "code",
            },
        }
        specials = ({"display_name", "__last_update", "company_id"} |
                    specials_mapping.get(name, set()))
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
        ignore = self.fields_to_ignore(template, template._name)
        for key, field in template._fields.iteritems():
            if key in ignore:
                continue
            expected = t = None
            # Translate template records to reals for comparison
            relation = field.get_description(self.env).get("relation", "")
            if relation:
                if ".tax.template" in relation:
                    t = "tax"
                elif ".account.template" in relation:
                    t = "account"
                if t:
                    find = getattr(
                        self,
                        "find_%s%s_by_templates" % (
                            "fp_" if ".fiscal.position" in relation
                            else "",
                            t))
                    if ".fiscal.position" in relation:
                        # Special case: if something is returned, then
                        # there's any difference, so it will get non equal
                        # when comparing, although we get the warning
                        # "Comparing apples with oranges"
                        expected = find(template[key], real[key])
                    else:
                        exp_id = find(template[key])
                        expected = self.env[relation[:-9]].browse(exp_id)
            # Register detected differences
            try:
                if expected is not None:
                    if expected != [] and expected != real[key]:
                        result[key] = expected
                elif template[key] != real[key]:
                    result[key] = template[key]
                # Avoid to cache recordset references
                if isinstance(real._fields[key], fields.Many2many):
                    result[key] = [(6, 0, result[key].ids)]
                elif isinstance(real._fields[key], fields.Many2one):
                    result[key] = result[key].id
            except KeyError:
                pass
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
            for f in self.diff_fields(template, real).keys())
        if different_fields:
            result.append(
                _("Differences in these fields: %s.") %
                ", ".join(different_fields))
        # Special for taxes
        if template._name == "account.tax.template":
            if not real.active:
                result.append(_("Tax is disabled."))
        return "\n".join(result)

    @api.multi
    def _find_taxes(self):
        """Search for, and load, tax templates to create/update/delete."""
        found_taxes_ids = []
        self.tax_ids.unlink()
        # Search for changes between template and real tax
        for template in self.chart_template_ids.\
                with_context(active_test=False).mapped("tax_template_ids"):
            # Check if the template matches a real tax
            tax_id = self.find_tax_by_templates(template)
            if not tax_id:
                # Tax to be created
                self.tax_ids.create({
                    'tax_id': template.id,
                    'update_chart_wizard_id': self.id,
                    'type': 'new',
                    'notes': _('Name or description not found.'),
                })
            else:
                found_taxes_ids.append(tax_id)
                # Check the tax for changes
                tax = self.env['account.tax'].browse(tax_id)
                notes = self.diff_notes(template, tax)
                if notes:
                    # Tax to be updated
                    self.tax_ids.create({
                        'tax_id': template.id,
                        'update_chart_wizard_id': self.id,
                        'type': 'updated',
                        'update_tax_id': tax_id,
                        'notes': notes,
                    })
        # search for taxes not in the template and propose them for
        # deactivation
        taxes_to_deactivate = self.env['account.tax'].search(
            [('company_id', '=', self.company_id.id),
             ("id", "not in", found_taxes_ids),
             ("active", "=", True)])
        for tax in taxes_to_deactivate:
            self.tax_ids.create({
                'update_chart_wizard_id': self.id,
                'type': 'deleted',
                'update_tax_id': tax.id,
                'notes': _("To deactivate: not in the template"),
            })

    @api.multi
    def _find_accounts(self):
        """Load account templates to create/update."""
        self.account_ids.unlink()
        for template in self.chart_template_ids.mapped("account_ids"):
            # Search for a real account that matches the template
            account_id = self.find_account_by_templates(template)
            if not account_id:
                # Account to be created
                self.account_ids.create({
                    'account_id': template.id,
                    'update_chart_wizard_id': self.id,
                    'type': 'new',
                    'notes': _('No account found with this code.'),
                })
            else:
                # Check the account for changes
                account = self.env['account.account'].browse(account_id)
                notes = self.diff_notes(template, account)
                if notes:
                    # Account to be updated
                    self.account_ids.create({
                        'account_id': template.id,
                        'update_chart_wizard_id': self.id,
                        'type': 'updated',
                        'update_account_id': account_id,
                        'notes': notes,
                    })

    @api.multi
    def _find_fiscal_positions(self):
        """Load fiscal position templates to create/update."""
        wiz_fp = self.env['wizard.update.charts.accounts.fiscal.position']
        self.fiscal_position_ids.unlink()

        # Search for new / updated fiscal positions
        templates = self.env['account.fiscal.position.template'].search(
            [('chart_template_id', 'in', self.chart_template_ids.ids)])
        for template in templates:
            # Search for a real fiscal position that matches the template
            fp_id = self.find_fp_by_templates(template)
            if not fp_id:
                # Fiscal position to be created
                wiz_fp.create({
                    'fiscal_position_id': template.id,
                    'update_chart_wizard_id': self.id,
                    'type': 'new',
                    'notes': _('No fiscal position found with this name.')
                })
            else:
                # Check the fiscal position for changes
                fp = self.env['account.fiscal.position'].browse(fp_id)
                notes = self.diff_notes(template, fp)
                if notes:
                    # Fiscal position template to be updated
                    wiz_fp.create({
                        'fiscal_position_id': template.id,
                        'update_chart_wizard_id': self.id,
                        'type': 'updated',
                        'update_fiscal_position_id': fp_id,
                        'notes': notes,
                    })

    @api.multi
    def _update_taxes(self):
        """Process taxes to create/update/deactivate."""
        for wiz_tax in self.tax_ids:
            template, tax = wiz_tax.tax_id, wiz_tax.update_tax_id
            # Deactivate tax
            if wiz_tax.type == 'deleted':
                tax.active = False
                _logger.info(_("Deactivated tax %s."), "'%s'" % tax.name)
                continue
            # Create tax
            if wiz_tax.type == 'new':
                template._generate_tax(self.company_id)
                _logger.info(_("Created tax %s."), "'%s'" % template.name)
            # Update tax
            else:
                for key, value in self.diff_fields(template, tax).iteritems():
                    # We defer update because account might not be created yet
                    if key in {'account_id', 'refund_account_id'}:
                        continue
                    tax[key] = value
                _logger.info(_("Updated tax %s."), "'%s'" % template.name)

    @api.multi
    def _update_accounts(self):
        """Process accounts to create/update."""
        for wiz_account in self.account_ids:
            account, template = (wiz_account.update_account_id,
                                 wiz_account.account_id)
            if wiz_account.type == 'new':
                # Create the account
                tax_template_ref = {
                    tax.id: self.find_tax_by_templates(tax) for tax in
                    template.tax_ids
                }
                vals = self.chart_template_id._get_account_vals(
                    self.company_id, template,
                    self.padded_code(template.code),
                    tax_template_ref,
                )
                try:
                    with self.env.cr.savepoint():
                        self.chart_template_id.create_record_with_xmlid(
                            self.company_id, template, 'account.account', vals,
                        )
                        _logger.info(
                            _("Created account %s."),
                            "'%s - %s'" % (vals['code'], vals['name']),
                        )
                except Exception:
                    self.rejected_new_account_number += 1
                    if config['test_enable']:
                        _logger.info(EXCEPTION_TEXT)
                    else:  # pragma: no cover
                        _logger.exception(
                            "ERROR: " + _("Exception creating account %s."),
                            "'%s - %s'" % (template.code, template.name),
                        )
                    if not self.continue_on_errors:
                        break
            else:
                # Update the account
                try:
                    with self.env.cr.savepoint():
                        for key, value in (self.diff_fields(template, account)
                                           .iteritems()):
                            account[key] = value
                            _logger.info(
                                _("Updated account %s."),
                                "'%s - %s'" % (account.code, account.name),
                            )
                except Exception:
                    self.rejected_updated_account_number += 1
                    if config['test_enable']:
                        _logger.info(EXCEPTION_TEXT)
                    else:  # pragma: no cover
                        _logger.exception(
                            "ERROR: " + _("Exception writing account %s."),
                            "'%s - %s'" % (account.code, account.name),
                        )
                    if not self.continue_on_errors:
                        break

    @api.multi
    def _update_taxes_pending_for_accounts(self):
        """Updates the taxes (created or updated on previous steps) to set
        the references to the accounts (the taxes where created/updated first,
        when the referenced accounts are still not available).
        """
        for wiz_tax in self.tax_ids:
            if wiz_tax.type == "deleted" or not wiz_tax.update_tax_id:
                continue
            template = wiz_tax.tax_id
            tax = wiz_tax.update_tax_id
            done = False
            for key, value in self.diff_fields(template, tax).iteritems():
                if key in {'account_id', 'refund_account_id'}:
                    tax[key] = value
                    done = True
            if done:
                _logger.info(_("Post-updated tax %s."), "'%s'" % tax.name)

    def _prepare_fp_vals(self, fp_template):
        # Tax mappings
        tax_mapping = []
        for fp_tax in fp_template.tax_ids:
            # Create the fp tax mapping
            tax_mapping.append({
                'tax_src_id': self.find_tax_by_templates(fp_tax.tax_src_id),
                'tax_dest_id': self.find_tax_by_templates(fp_tax.tax_dest_id),
            })
        # Account mappings
        account_mapping = []
        for fp_account in fp_template.account_ids:
            # Create the fp account mapping
            account_mapping.append({
                'account_src_id': (
                    self.find_account_by_templates(fp_account.account_src_id)
                ),
                'account_dest_id': (
                    self.find_account_by_templates(fp_account.account_dest_id)
                ),
            })
        return {
            'company_id': self.company_id.id,
            'name': fp_template.name,
            'tax_ids': [(0, 0, x) for x in tax_mapping],
            'account_ids': [(0, 0, x) for x in account_mapping],
        }

    @api.multi
    def _update_fiscal_positions(self):
        """Process fiscal position templates to create/update."""
        for wiz_fp in self.fiscal_position_ids:
            fp, template = (wiz_fp.update_fiscal_position_id,
                            wiz_fp.fiscal_position_id)
            if wiz_fp.type == 'new':
                # Create a new fiscal position
                self.chart_template_id.create_record_with_xmlid(
                    self.company_id, template, 'account.fiscal.position',
                    self._prepare_fp_vals(template),
                )
            else:
                # Update the given fiscal position
                for key, value in self.diff_fields(template, fp).iteritems():
                    fp[key] = value
            _logger.info(
                _("Created or updated fiscal position %s."),
                "'%s'" % template.name)


class WizardUpdateChartsAccountsTax(models.TransientModel):
    _name = 'wizard.update.charts.accounts.tax'
    _description = ("Tax that needs to be updated (new or updated in the "
                    "template).")

    tax_id = fields.Many2one(
        comodel_name='account.tax.template', string='Tax template',
        ondelete='set null')
    update_chart_wizard_id = fields.Many2one(
        comodel_name='wizard.update.charts.accounts',
        string='Update chart wizard', required=True, ondelete='cascade')
    type = fields.Selection(
        selection=[('new', 'New template'),
                   ('updated', 'Updated template'),
                   ('deleted', 'Tax to deactivate')],
        string='Type',
        readonly=True)
    type_tax_use = fields.Selection(
        related="tax_id.type_tax_use",
        readonly=True)
    update_tax_id = fields.Many2one(
        comodel_name='account.tax', string='Tax to update', required=False,
        ondelete='set null')
    notes = fields.Text('Notes', readonly=True)


class WizardUpdateChartsAccountsAccount(models.TransientModel):
    _name = 'wizard.update.charts.accounts.account'
    _description = ("Account that needs to be updated (new or updated in the "
                    "template).")

    account_id = fields.Many2one(
        comodel_name='account.account.template', string='Account template',
        required=True, ondelete='set null')
    update_chart_wizard_id = fields.Many2one(
        comodel_name='wizard.update.charts.accounts',
        string='Update chart wizard', required=True, ondelete='cascade'
    )
    type = fields.Selection(
        selection=[('new', 'New template'),
                   ('updated', 'Updated template')],
        string='Type',
        readonly=True)
    update_account_id = fields.Many2one(
        comodel_name='account.account', string='Account to update',
        required=False, ondelete='set null')
    notes = fields.Text('Notes', readonly=True)


class WizardUpdateChartsAccountsFiscalPosition(models.TransientModel):
    _name = 'wizard.update.charts.accounts.fiscal.position'
    _description = ("Fiscal position that needs to be updated (new or updated "
                    "in the template).")

    fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position.template',
        string='Fiscal position template', required=True, ondelete='set null')
    update_chart_wizard_id = fields.Many2one(
        comodel_name='wizard.update.charts.accounts',
        string='Update chart wizard', required=True, ondelete='cascade')
    type = fields.Selection(
        selection=[('new', 'New template'),
                   ('updated', 'Updated template')],
        string='Type', readonly=True, required=True,
    )
    update_fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position', required=False,
        string='Fiscal position to update', ondelete='set null')
    notes = fields.Text('Notes', readonly=True)
