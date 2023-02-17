# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from sys import exc_info
from traceback import format_exception

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AssetComputeBatch(models.Model):
    _name = "account.asset.compute.batch"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Compute Depreciation Batch"
    _check_company_auto = True

    name = fields.Char(
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    description = fields.Char(
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    date_end = fields.Date(
        string="Date",
        required=True,
        default=fields.Date.today,
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="All depreciation lines prior to this date will be computed",
    )
    note = fields.Text(string="Exception Error")
    profile_ids = fields.Many2many(
        comodel_name="account.asset.profile",
        string="Profiles",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Selected asset to run depreciation. Run all profiles if left blank.",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        readonly=True,
        default=lambda self: self.env.company,
    )
    delay_post = fields.Boolean(
        string="Delay Posting",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Dalay account posting of newly created journaly entries, "
        "by setting auto_post=True, to be posted by cron job",
    )
    auto_compute = fields.Boolean(
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Auto compute draft batches with 'Date' up to today, by cron job",
    )
    move_line_ids = fields.One2many(
        comodel_name="account.move.line",
        inverse_name="compute_batch_id",
        readonly=True,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("computed", "Computed"),
            ("exception", "Exception"),
        ],
        default="draft",
        tracking=True,
        index=True,
        required=True,
        readonly=True,
    )
    profile_report = fields.One2many(
        comodel_name="account.asset.compute.batch.profile.report",
        inverse_name="compute_batch_id",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        default=lambda self: self.env.company.currency_id,
    )
    depre_amount = fields.Monetary(
        string="Depreciation Amount",
        compute="_compute_depre_amount",
    )
    _sql_constraints = [
        ("name_uniq", "UNIQUE(name)", "Batch name must be unique!"),
    ]

    @api.depends("state")
    def _compute_depre_amount(self):
        res = self.env["account.move.line"].read_group(
            [("compute_batch_id", "in", self.ids)],
            ["compute_batch_id", "debit"],
            ["compute_batch_id"],
        )
        res = {x["compute_batch_id"][0]: x["debit"] for x in res}
        for rec in self:
            rec.depre_amount = res.get(rec.id)

    def unlink(self):
        if self.filtered(lambda l: l.state != "draft"):
            raise ValidationError(_("Only draft batch can be deleted!"))
        return super().unlink()

    def action_compute(self):
        for batch in self:
            assets = self.env["account.asset"].search([("state", "=", "open")])
            created_move_ids, error_log = assets.with_context(
                compute_batch_id=batch.id,
                compute_profile_ids=batch.profile_ids.ids,
                delay_post=batch.delay_post,
            )._compute_entries(self.date_end, check_triggers=True)
            if error_log:
                batch.note = _("Compute Assets errors") + ":\n" + error_log
                batch.state = "exception"
            else:
                batch.state = "computed"

    def open_move_lines(self):
        self.ensure_one()
        action = {
            "name": _("Journal Items"),
            "view_type": "tree",
            "view_mode": "list,form",
            "res_model": "account.move.line",
            "type": "ir.actions.act_window",
            "context": {"search_default_group_by_account": True},
            "domain": [("id", "in", self.move_line_ids.ids)],
        }
        return action

    def open_moves(self):
        self.ensure_one()
        action = {
            "name": _("Journal Entries"),
            "view_type": "tree",
            "view_mode": "list,form",
            "res_model": "account.move",
            "type": "ir.actions.act_window",
            "context": {},
            "domain": [("id", "in", self.move_line_ids.mapped("move_id").ids)],
        }
        return action

    @api.model
    def _autocompute_draft_batches(self):
        """This method is called from a cron job.
        It is used to auto compute account.asset.compute.batch with auto_compute=True
        """
        records = self.search(
            [
                ("state", "=", "draft"),
                ("date_end", "<=", fields.Date.context_today(self)),
                ("auto_compute", "=", True),
            ]
        )
        for ids in self.env.cr.split_for_in_conditions(records.ids, size=1000):
            batches = self.browse(ids)
            try:
                with self.env.cr.savepoint():
                    batches.action_compute()
            except Exception:
                exc_info()[0]
                tb = "".join(format_exception(*exc_info()))
                batch_ref = ", ".join(batches.mapped("name"))
                error_msg = _(
                    "Error while processing batches %(batch_ref)s: \n\n%(tb)s"
                ) % {"batch_ref": batch_ref, "tb": tb}
                _logger.error("%s, %s", self._name, error_msg)


class AccountAssetComputeBatchProfileReport(models.Model):
    _name = "account.asset.compute.batch.profile.report"
    _description = "Depreciation Amount by Profile"
    _auto = False
    _order = "profile_id desc"

    compute_batch_id = fields.Many2one(
        comodel_name="account.asset.compute.batch",
        readonly=True,
    )
    profile_id = fields.Many2one(
        string="Asset Profile",
        comodel_name="account.asset.profile",
        readonly=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        readonly=True,
    )
    amount = fields.Monetary(
        readonly=True,
    )

    @property
    def _table_query(self):
        return "%s %s %s %s" % (
            self._select(),
            self._from(),
            self._where(),
            self._group_by(),
        )

    @api.model
    def _select(self):
        return """
            SELECT
                min(ml.id) as id,
                compute_batch_id,
                p.id as profile_id,
                currency_id,
                sum(debit) as amount
        """

    @api.model
    def _from(self):
        return """
            FROM account_move_line ml
                JOIN account_asset a on a.id = ml.asset_id
                JOIN account_asset_profile p on p.id = a.profile_id
        """

    @api.model
    def _where(self):
        return """
            WHERE
                compute_batch_id IS NOT NULL
        """

    @api.model
    def _group_by(self):
        return """
            GROUP BY
                compute_batch_id,
                p.id,
                currency_id
        """
