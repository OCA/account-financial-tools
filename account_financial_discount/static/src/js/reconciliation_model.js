odoo.define('account_financial_discount.ReconciliationModel', function (require) {
"use strict";

var ReconciliationModel = require('account.ReconciliationModel');
var field_utils = require('web.field_utils');

ReconciliationModel.StatementModel.include({

    _formatFinancialDiscountTaxQuickCreate: function(line) {
        var tax_amount = -line.reconciliation_proposition[0].amount_discount_tax;
        var tax_account = line.reconciliation_proposition[0].discount_tax_line_account_id;
        var tax_label = line.reconciliation_proposition[0].discount_tax_line_name;
        var today = new moment().utc().format();
        var account = this._formatNameGet(tax_account);
        var formatOptions = {
            currency_id: line.st_line.currency_id,
        };
        var prop = {
            'id': _.uniqueId('createLine'),
            'label': tax_label,
            'account_id': account,
            'account_code': account ? this.accounts[account.id] : '',
            // TODO: Check if we want to add fin disc analytic, taxes, tags?
            // 'analytic_account_id': this._formatNameGet(values.analytic_account_id),
            'analytic_tag_ids': this._formatMany2ManyTags([]),
            'journal_id': false,
            'tax_ids': this._formatMany2ManyTagsTax([]),
            // 'tag_ids': values.tag_ids,
//            'tax_repartition_line_id': values.tax_repartition_line_id,
            'debit': 0,
            'credit': 0,
            'date': field_utils.parse.date(today, {}, {isUTC: true}),
            'force_tax_included': false,
            'base_amount': tax_amount,
//            'percent': values.amount_type === "percentage" ? values.amount : null,
            // FIXME defining link should allow to restore proposition after removal
            //   but somehow we don't see the proposition anymore after removal while
            //   it is set
            //'link': line.reconciliation_proposition[0].id,
            'display': true,
            'invalid': false,
            'to_check': false,
            '__tax_to_recompute': true,
            '__focus': true,
        };
        if (prop.base_amount) {
            // Call to format and parse needed to round the value to the currency precision
            var sign = prop.base_amount < 0 ? -1 : 1;
            var amount = field_utils.format.monetary(Math.abs(prop.base_amount), {}, formatOptions);
            prop.base_amount = sign * field_utils.parse.monetary(amount, {}, formatOptions);
        }

        prop.amount = prop.base_amount;
        return prop;
    },
    _formatFinancialDiscountQuickCreate: function(line, values) {
        values = values || {};
        if (values && values.journal_id === undefined && line && line.createForm && line.createForm.journal_id) {
            values.journal_id = line.createForm.journal_id;
        }
        var today = new moment().utc().format();
        var amount_discount = -line.reconciliation_proposition[0].amount_discount + line.reconciliation_proposition[0].amount_discount_tax;
        var fin_disc_account = amount_discount < 0 ? values.financial_discount_expense_account_id : values.financial_discount_revenue_account_id
        var account = this._formatNameGet(fin_disc_account);
        var formatOptions = {
            currency_id: line.st_line.currency_id,
        };
        var prop = {
            'id': _.uniqueId('createLine'),
            'label': values.financial_discount_label || line.st_line.name,
            'account_id': account,
            'account_code': account ? this.accounts[account.id] : '',
            // TODO: Check if we want to add fin disc analytic, taxes, tags?
            // 'analytic_account_id': this._formatNameGet(values.analytic_account_id),
            'analytic_tag_ids': this._formatMany2ManyTags([]),
            'journal_id': this._formatNameGet(values.journal_id),
            'tax_ids': this._formatMany2ManyTagsTax([]),
            // 'tag_ids': values.tag_ids,
//            'tax_repartition_line_id': values.tax_repartition_line_id,
            'debit': 0,
            'credit': 0,
            'date': values.date ? values.date : field_utils.parse.date(today, {}, {isUTC: true}),
            'force_tax_included': false,
            'base_amount': amount_discount,
//            'percent': values.amount_type === "percentage" ? values.amount : null,
            // FIXME defining link should allow to restore proposition after removal
            //   but somehow we don't see the proposition anymore after removal while
            //   it is set
//            'link': line.reconciliation_proposition[0].id,
            'display': true,
            'invalid': false,
            'to_check': false,
            '__tax_to_recompute': false,
            '__focus': false,
        };
        if (prop.base_amount) {
            // Call to format and parse needed to round the value to the currency precision
            var sign = prop.base_amount < 0 ? -1 : 1;
            var amount = field_utils.format.monetary(Math.abs(prop.base_amount), {}, formatOptions);
            prop.base_amount = sign * field_utils.parse.monetary(amount, {}, formatOptions);
        }

        prop.amount = prop.base_amount;
        return prop;
    },
    quickCreateProposition: function (handle, reconcileModelId) {
        var self = this;
        var line = this.getLine(handle);
        if (line.reconciliation_proposition.length && line.reconciliation_proposition[0].financial_discount_available && !line.createForm) {
            // Create proposition with fin disc write off accounts
            var reconcileModel = _.find(this.reconcileModels, function (r) {return r.id === reconcileModelId;});
            var fields = ['financial_discount_label', 'financial_discount_revenue_account_id', 'financial_discount_expense_account_id', 'financial_discount_tolerance']
            this._blurProposition(handle);
            // TODO Fix the mess with taxes
            var focus = this._formatFinancialDiscountQuickCreate(line, _.pick(reconcileModel, fields));
            focus.reconcileModelId = reconcileModelId;
            line.reconciliation_proposition.push(focus);
            var defs = [];
            if (line.reconciliation_proposition[0].amount_discount_tax) {
                defs.push(
                    self._computeLine(line).then(function() {
                        var tax_focus = self._formatFinancialDiscountTaxQuickCreate(line);
                        tax_focus.reconcileModelId = reconcileModelId;
                        line.reconciliation_proposition.push(tax_focus);
                        self._computeReconcileModels(handle, reconcileModelId);
                    })
                )
            }
            return Promise.all(defs).then(function() {
                line.createForm = _.pick(focus, self.quickCreateFields);
                return self._computeLine(line);
            })
        } else {
            // Call super if called from createForm
            return this._super(handle, reconcileModelId);
        }
    },
});

});
