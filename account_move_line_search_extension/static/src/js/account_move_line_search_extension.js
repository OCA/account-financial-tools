openerp.account_move_line_search_extension = function (instance) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;
    
    instance.account_move_line_search_extension = {};

    instance.web.views.add('account_move_line_search_extension', 'instance.account_move_line_search_extension.ListSearchView');
    instance.account_move_line_search_extension.ListSearchView = instance.web.ListView.extend({
    
        init: function() {
            this._super.apply(this, arguments);
            this.journals = [];
            this.current_account = null;
            this.current_partner = null;
            this.current_journal = null;
            this.current_period = null;
        },
        
        start:function(){
            var tmp = this._super.apply(this, arguments);
            var self = this;
            this.$el.parent().prepend(QWeb.render('AccountMoveLineSearchExtension', {widget: this}));
                 
            this.$el.parent().find('.oe_account_select_account').change(function() {
                    self.current_account = this.value === '' ? null : this.value;
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });
            this.$el.parent().find('.oe_account_select_partner').change(function() {
                    self.current_partner = this.value === '' ? null : this.value;
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });        
            this.$el.parent().find('.oe_account_select_journal').change(function() {
                    self.current_journal = this.value === '' ? null : parseInt(this.value);
                    //console.log('start, oasj, self.current_journal=', self.current_journal, 'self.last_domain=', self.last_domain, 'self.last_context=', self.last_context, 'self.last_group_by=', self.last_group_by);
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });
            this.$el.parent().find('.oe_account_select_period').change(function() {
                    self.current_period = this.value === '' ? null : this.value;
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });
            this.on('edit:after', this, function () {
                self.$el.parent().find('.oe_account_select_account').attr('disabled', 'disabled');
                self.$el.parent().find('.oe_account_select_partner').attr('disabled', 'disabled');
                self.$el.parent().find('.oe_account_select_journal').attr('disabled', 'disabled');
                self.$el.parent().find('.oe_account_select_period').attr('disabled', 'disabled');
            });
            this.on('save:after cancel:after', this, function () {
                self.$el.parent().find('.oe_account_select_account').removeAttr('disabled');
                self.$el.parent().find('.oe_account_select_partner').removeAttr('disabled');
                self.$el.parent().find('.oe_account_select_journal').removeAttr('disabled');
                self.$el.parent().find('.oe_account_select_period').removeAttr('disabled');
            });
            return tmp;
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
        
        search_by_selection: function() {
            var self = this;
            var domain = [];
            if (self.current_account) domain.push(['account_id.code', 'ilike', self.current_account]);
            if (self.current_partner) domain.push(['partner_id.name', 'ilike', self.current_partner],'|',['partner_id.parent_id','=',false],['partner_id.is_company','=',true]);            
            if (self.current_journal) domain.push(['journal_id', '=', self.current_journal]);
            if (self.current_period) domain.push('|',['period_id.code', 'ilike', self.current_period],['period_id.name', 'ilike', self.current_period]);
            //_.each(domain, function(x) {console.log('search_by_journal_period, domain_part = ', x)}); 
            return self.old_search(new instance.web.CompoundDomain(self.last_domain, domain), self.last_context, self.last_group_by);
        },
        
    });
};
