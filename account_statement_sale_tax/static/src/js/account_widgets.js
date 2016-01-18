
openerp.account_statement_sale_tax = function (instance) {
    instance.web.account.bankStatementReconciliation.include({
        init: function(parent, context) {
            this._super.apply(this, arguments);
            this.create_form_fields.tax_id.field_properties.domain = [['parent_id', '=', false]];
        },
    });
};
