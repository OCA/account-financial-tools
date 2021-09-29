/*
# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/

odoo.define('account_move_line_search_extension.amlse', function (require) {
    "use strict";

    var core = require('web.core');
    var BasicView = require('web.BasicView');
    var ListView = require('web.ListView');
    var ListRenderer = require('web.ListRenderer');
    var ListController = require('web.ListController');
    var SearchView = require('web.SearchView');
    var view_registry = require('web.view_registry');
    var QWeb = core.qweb;
    var datepicker = require('web.datepicker');

    SearchView.include({

        build_search_data: function () {
            var search_data = this._super.apply(this);
            if (this.amlse_domain) {
                search_data.domains.push(this.amlse_domain);
            }
            return search_data;
        },

    });

    var amlseListRenderer = ListRenderer.extend({

        init: function (parent, state, params) {
            /*
            The ListRenderer requires fieldsInfo['list'] when a widget is set on a list view.
            Cf. code block:
            if (node.attrs.widget) {
                description = this.state.fieldsInfo.list[name].Widget.prototype.description;
            The OCA module 'web_tree_many2one_clickable' adds the many2one widget to list view cells resulting
            in a js error when we do not initialise fieldsInfo['list'].
            */
            this._super.apply(this, arguments);
            this.state.fieldsInfo['list'] = this.state.fieldsInfo['amlse'];
        },

    });

    var amlseController = ListController.extend({

        init: function (parent, model, renderer, params) {
            this._super.apply(this, arguments);
            this.searchview = parent.action.viewManager.searchview;
            this.current_account = null;
            this.current_analytic_account = null;
            this.current_partner = null;
            this.journals = [];
            this.current_journal = null;
            this.date_ranges = [];
            this.current_date_before = null;
            this.current_date_after = null;
            this.current_date_range = null;
            this.current_reconcile = null;
            this.current_amount = null;
        },

        start: function () {
            this._super.apply(this, arguments);
            var self = this;
            return $.when(this.get_render_dict()).then(function (render_dict) {
                self.$el.parent().prepend(QWeb.render('AccountMoveLineSearchExtension', render_dict));
                self._rpc({
                    model: 'account.journal',
                    method: 'search_read',
                    fields: ['name'],
                }).then(function (result) {
                    self.journals = result;
                    var oesj = self.$el.parent().find('.oe_account_select_journal')
                    oesj.children().remove().end();
                    oesj.append(new Option('', ''));
                    for (var i = 0; i < self.journals.length; i++) {
                        var o = new Option(self.journals[i].name, self.journals[i].id);
                        oesj.append(o);
                    };
                });
                self._rpc({
                    model: 'date.range',
                    method: 'search_read',
                    fields: ['name', 'date_start', 'date_end'],
                }).then(function (result) {
                    self.date_ranges = result;
                    var oesdr = self.$el.parent().find('.oe_account_select_date_range')
                    oesdr.children().remove().end();
                    oesdr.append(new Option('', ''));
                    for (var i = 0; i < self.date_ranges.length; i++) {
                        var o = new Option(self.date_ranges[i].name, i + 1);
                        oesdr.append(o);
                    };
                });
                self.set_change_events();
            });
        },

        set_change_events: function () {
            var self = this;
            this.$el.parent().find('.oe_account_select_account').change(function () {
                self.current_account = this.value === '' ? null : this.value;
                self.do_search();
            });
            this.$el.parent().find('.oe_account_select_analytic_account').change(function () {
                self.current_analytic_account = this.value === '' ? null : this.value;
                self.do_search();
            });
            this.$el.parent().find('.oe_account_select_partner').change(function () {
                self.current_partner = this.value === '' ? null : this.value;
                self.do_search();
            });
            this.$el.parent().find('.oe_account_select_journal').change(function () {
                self.current_journal = this.value === '' ? null : parseInt(this.value);
                self.do_search();
            });
            this.$el.parent().find('.oe_account_select_date_range').change(function () {
                self.current_date_range = this.value === '' ? null : parseInt(this.value);
                self.do_search();
            });
            this.$el.parent().find('.oe_account_select_reconcile').change(function () {
                self.current_reconcile = this.value === '' ? null : this.value;
                self.do_search();
            });
            this.$el.parent().find('.oe_account_select_amount').change(function () {
                self.current_amount = this.value === '' ? null : this.value;
                self.do_search();
            });
            /*
            this.datewidget_b = new datepicker.DateWidget(this, {defaultDate: this.value});;
            this.datewidget_b.on('click', this, function () {
                var value = this.datewidget.getValue();
                if ((!value && this.value) || (value && !value.isSame(this.value, 'day'))) {
                    self.current_date_before = this.value === '' ? null : this.value;
                    self.do_search();
                }
            });
            this.datewidget_b.$input = $("<input type='text'/>");
            this.datewidget_b.$input.addClass('o_datepicker_input oe_account_select_date_before');
            this.datewidget_b.$input.val(this.value);
            this.$el.parent().find('.oe_account_select_date_before').replaceWith(self.datewidget_b.$input);
            console.log("DATE BEFORE", self.datewidget_b.$input);
             */
            this.$el.parent().find('.oe_account_select_date_before').change(function () {
                self.current_date_before = this.value === '' ? null : this.value;
                self.do_search();
            });
            this.$el.parent().find('.oe_account_select_date_after').change(function () {
                self.current_date_after = this.value === '' ? null : this.value;
                self.do_search();
            });
        },

        get_render_dict: function () {
            /*
            Customise this function to modify the rendering dict for the qweb template.
            By default the action context is merged into the result of the 'account.move.line, get_amlse_render_dict()' method.
            */
            var self = this;
            return this._rpc({
                model: 'account.move.line',
                method: 'get_amlse_render_dict',
            }).then(function (result) {
                var render_dict = _.extend(result, self.initialState.context);
                return render_dict;
            });
        },

        do_search: function () {
            var amlse_domain = this.aml_search_domain();
            this.searchview.amlse_domain = amlse_domain;
            this.searchview.do_search();
        },

        aml_search_domain: function () {
            var domain = [];
            if (this.current_account) domain.push(['account_id.code', 'ilike', this.current_account]);
            if (this.current_analytic_account) domain.push(['analytic_account_search', 'in', this.current_analytic_account]);
            if (this.current_partner) domain.push(['partner_id.name', 'ilike', this.current_partner]);
            if (this.current_journal) domain.push(['journal_id', '=', this.current_journal]);
            if (this.current_date_range) {
                var dr = this.date_ranges[this.current_date_range - 1];
                domain.push('&', ['date', '>=', dr.date_start], ['date', '<=', dr.date_end]);
            };
            if (this.current_date_before && this.current_date_after) {
                domain.push('&', ['date', '>=', this.current_date_after], ['date', '<=', this.current_date_before]);
            } else {
                if (this.current_date_before) domain.push(['date', '<=', this.current_date_before]);
                if (this.current_date_after) domain.push(['date', '>=', this.current_date_after]);
            };
            if (this.current_reconcile) domain.push(['full_reconcile_id.name', '=ilike', this.current_reconcile]);
            if (this.current_amount) domain.push(['amount_search', '=', this.current_amount]);
            //_.each(domain, function(x) {console.log('amlse, aml_search_domain, domain_part = ', x)});
            return domain;
        },

    });

    var amlseListSearchView = ListView.extend({

        config: _.extend({}, BasicView.prototype.config, {
            Renderer: amlseListRenderer,
            Controller: amlseController,
        }),
        viewType: 'amlse',

    });

    view_registry.add('amlse', amlseListSearchView);

    return {
        amlseController: amlseController,
        amlseListSearchView: amlseListSearchView,
        amlseListRenderer: amlseListRenderer,
    };

});
