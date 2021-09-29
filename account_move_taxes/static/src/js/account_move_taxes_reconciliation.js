odoo.define('account_move_taxes.reconciliation', function (require) {
"use strict";

var ReconciliationModel = require('account.ReconciliationModel');
var ReconciliationRenderer = require('account.ReconciliationRenderer');

var Widget = require('web.Widget');
var FieldManagerMixin = require('web.FieldManagerMixin');
var relational_fields = require('web.relational_fields');
var basic_fields = require('web.basic_fields');
var core = require('web.core');
var time = require('web.time');
var qweb = core.qweb;
var _t = core._t;

ReconciliationModel.StatementModel.include({
    init: function () {
        this._super.apply(this, arguments);
        this.quickCreateFields.push('tax_included');
        console.log('FIELDS', this.quickCreateFields);
    },
});
ReconciliationModel.ManualModel.include({
    init: function () {
        this._super.apply(this, arguments);
        this.quickCreateFields.push('tax_included');
        console.log('FIELDS', this.quickCreateFields);
    },
});
ReconciliationRenderer.LineRenderer.include({
    /**
     * create account_id, tax_id, analytic_account_id, label, amount and tax_included field
     *
     * @private
     * @param {object} state - statement line
     */
    _renderCreate: function (state) {
        var self = this;
        this.model.makeRecord('account.bank.statement.line', [{
            relation: 'account.account',
            type: 'many2one',
            name: 'account_id',
        }, {
            relation: 'account.journal',
            type: 'many2one',
            name: 'journal_id',
        }, {
            relation: 'account.tax',
            type: 'many2one',
            name: 'tax_id',
        }, {
            relation: 'account.analytic.account',
            type: 'many2one',
            name: 'analytic_account_id',
        }, {
            type: 'char',
            name: 'label',
        }, {
            type: 'float',
            name: 'amount',
        }, {
            type: 'boolean',
            name: 'tax_included',
        }], {
            account_id: {
                string: _t("Account"),
                domain: [['deprecated', '=', false]],
            },
            label: {string: _t("Label")},
            amount: {string: _t("Account")}
        }).then(function (recordID) {
            self.handleCreateRecord = recordID;
            var record = self.model.get(self.handleCreateRecord);

            self.fields.account_id = new relational_fields.FieldMany2One(self,
                'account_id', record, {mode: 'edit'});

            self.fields.journal_id = new relational_fields.FieldMany2One(self,
                'journal_id', record, {mode: 'edit'});

            self.fields.tax_id = new relational_fields.FieldMany2One(self,
                'tax_id', record, {mode: 'edit'});

            self.fields.analytic_account_id = new relational_fields.FieldMany2One(self,
                'analytic_account_id', record, {mode: 'edit'});

            self.fields.label = new basic_fields.FieldChar(self,
                'label', record, {mode: 'edit'});

            self.fields.amount = new basic_fields.FieldFloat(self,
                'amount', record, {mode: 'edit'});

            self.fields.tax_included = new basic_fields.FieldBoolean(self,
                'tax_included', record, {mode: 'edit'});

            var $create = $(qweb.render("reconciliation.line.create", {'state': state}));
            self.fields.account_id.appendTo($create.find('.create_account_id .o_td_field'))
                .then(addRequiredStyle.bind(self, self.fields.account_id));
            self.fields.journal_id.appendTo($create.find('.create_journal_id .o_td_field'));
            self.fields.tax_id.appendTo($create.find('.create_tax_id .o_td_field'));
            self.fields.analytic_account_id.appendTo($create.find('.create_analytic_account_id .o_td_field'));
            self.fields.label.appendTo($create.find('.create_label .o_td_field'))
                .then(addRequiredStyle.bind(self, self.fields.label));
            self.fields.amount.appendTo($create.find('.create_amount .o_td_field'))
                .then(addRequiredStyle.bind(self, self.fields.amount));
            self.fields.tax_included.appendTo($create.find('.create_tax_included .o_td_field'))
                .then(addRequiredStyle.bind(self, self.fields.tax_included));
            self.$('.create').append($create);

            function addRequiredStyle(widget) {
                widget.$el.addClass('o_required_modifier');
            }
        });
    },
});
});