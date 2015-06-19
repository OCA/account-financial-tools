openerp.account_move_line_search_extension = function (instance) {
    var QWeb = instance.web.qweb;

    instance.account_move_line_search_extension = {};

    instance.web.views.add('account_move_line_search_extension', 'instance.account_move_line_search_extension.ListSearchView');
    instance.account_move_line_search_extension.ListSearchView = instance.web.ListView.extend({

        init: function() {
            var self = this;
            this._super.apply(this, arguments);
            this.journals = [];
            this.current_account = null;
            this.current_analytic_account = null;
            this.current_partner = null;
            this.current_journal = null;
            this.current_period = null;
            this.options.addable = false;
            this.set_user_groups();
        },

        start: function(){
            var tmp = this._super.apply(this, arguments);
            var self = this;
            this.$el.parent().prepend(QWeb.render('AccountMoveLineSearchExtension', self.groups_dict));
            self.set_change_events();
            return tmp;
        },

        set_change_events: function() {
            var self = this;
            this.$el.parent().find('.oe_account_select_account').change(function() {
                    self.current_account = this.value === '' ? null : this.value;
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });
             this.$el.parent().find('.oe_account_select_analytic_account').change(function() {
                    self.current_analytic_account = this.value === '' ? null : this.value;
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });
            this.$el.parent().find('.oe_account_select_partner').change(function() {
                    self.current_partner = this.value === '' ? null : this.value;
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });
            this.$el.parent().find('.oe_account_select_journal').change(function() {
                    self.current_journal = this.value === '' ? null : parseInt(this.value);
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });
            this.$el.parent().find('.oe_account_select_period').change(function() {
                    self.current_period = this.value === '' ? null : this.value;
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });
        },

        set_user_groups: function() {
            var self = this;
            var result = {};
            var action_context = this.dataset.get_context().__contexts[1];
            _.each(action_context, function(v,k) {
                if (k[v] && (k.slice(0, 6) === "group_")) {
                    result[k] = true;
                }
                else {
                    result[k] = false;
                };
            });
            self.groups_dict = result;
        },

        do_search: function(domain, context, group_by) {
            var self = this;
            this.last_domain = domain;
            this.last_context = context;
            this.last_group_by = group_by;
            this.old_search = _.bind(this._super, this);
            var aj_mod = new instance.web.Model('account.journal');
            return $.when(aj_mod.query(['name']).all().then(function(result) {
                self.journals = result;
            })).then(function () {
                var o;
                self.$el.parent().find('.oe_account_select_journal').children().remove().end();
                self.$el.parent().find('.oe_account_select_journal').append(new Option('', ''));
                for (var i = 0;i < self.journals.length;i++){
                    o = new Option(self.journals[i].name, self.journals[i].id);
                    if (self.journals[i].id === self.current_journal){
                        $(o).attr('selected',true);
                    }
                    self.$el.parent().find('.oe_account_select_journal').append(o);
                }
                return self.search_by_selection();
            });
        },

        aml_search_domain: function() {
            var self = this;
            var domain = [];
            if (self.current_account) domain.push(['account_id.code', 'ilike', self.current_account]);
            if (self.current_analytic_account) domain.push(['analytic_account_id', 'in', self.current_analytic_account]); //cf. def search
            if (self.current_partner) domain.push(['partner_id.name', 'ilike', self.current_partner]);
            if (self.current_journal) domain.push(['journal_id', '=', self.current_journal]);
            if (self.current_period) domain.push('|',['period_id.code', 'ilike', self.current_period],['period_id.name', 'ilike', self.current_period]);
            //_.each(domain, function(x) {console.log('amlse, aml_search_domain, domain_part = ', x)});
            return domain;
        },

        search_by_selection: function() {
            var self = this;
            var domain = self.aml_search_domain();
            return self.old_search(new instance.web.CompoundDomain(self.last_domain, domain), self.last_context, self.last_group_by);
        },

    });
};
