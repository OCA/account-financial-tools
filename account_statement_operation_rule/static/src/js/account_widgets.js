openerp.account_statement_operation_rule = function (instance) {

    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    instance.web.account_statement_operation_rule = instance.web.account_statement_operation_rule || {};

    instance.web.account.bankStatementReconciliationLine.include({
        operation_rules: function() {
            var self = this;
            var model_operation_rule = new instance.web.Model("account.statement.operation.rule");
            model_operation_rule.call("operations_for_reconciliation",
                                      [self.st_line.id,
                                       _.pluck(self.get("mv_lines_selected"), 'id')])
                .then(function (operations) {
                    _.each(operations, function(operation_id) {
                        preset_btn = self.$("button.preset[data-presetid='" + operation_id + "']");
                        preset_btn.click();
                        self.addLineBeingEdited();
                    });
                });
            // if (self.is_valid) {
            //     self.persistAndDestroy();
            // }
        },
        render: function() {
            deferred = this._super();
            if (deferred) {
                deferred.done(this.operation_rules());
            }
            return deferred;
        },
        restart: function() {
            deferred = this._super();
            deferred.done(this.operation_rules());
            return deferred;
        },
    });
};
