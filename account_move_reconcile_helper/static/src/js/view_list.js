openerp.account_move_reconcile_helper = function(instance) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    instance.web.ListView.include({ 
    
        dh : function (n){
            var hex = (255-n).toString(16).toUpperCase();
            if (hex.length==1) {
                    hex='0'+hex;
            }
            return (hex);
        },
        
        inverse_color: function (couleur) {
            
            var r = /#?(\w{2})(\w{2})(\w{2})/i;
            var splitH = r.exec(couleur);
    
            var ar=16*Number('0x'+splitH[1].slice(0,1))+Number('0x'+splitH[1].slice(1,2));
            var br=16*Number('0x'+splitH[2].slice(0,1))+Number('0x'+splitH[2].slice(1,2));
            var cr=16*Number('0x'+splitH[3].slice(0,1))+Number('0x'+splitH[3].slice(1,2));
    
            return ('#'+this.dh(ar)+this.dh(br)+this.dh(cr));
    
        },

        get_colors: function(){
            return ['#FFFF99', '#FF66FF', '#FF9966', '#FF9900',
                    '#CCFFFF', '#FF0000', '#006600', '#FF3333',
                    '#000000', '#666699', '#996633', '#CC3399', 
                    '#CCCC99', '#CCCC00', '#339966', '#FFCCCC',
                    '#00FFFF', '#009999', '#FFCC66', '#3366CC',
                    '#996666', '#99CC66', '#FF3366', '#339933',
                    '#6666FF', '#009900', '#CC33CC', '#99CCCC',
                    '#FF6633', '#33CC99', '#333333', '#99FF66',
                    '#FF6666', '#660099', '#669933', '#FF0033']
        },
    
        style_cell: function(record, column){
            style = ''
            if (this.model == 'account.move.line' && column.name == 'reconcile_ref' && record.get(column.name)) {
                
                reconcile_id = record.get('reconcile_id')
                if (reconcile_id == false) {
                    reconcile_id = record.get('reconcile_partial_id')
                }
                
                if (reconcile_id != false && reconcile_id != undefined) {
                    colors = this.get_colors()
                    bgcolor = colors[reconcile_id[0] % colors.length]
                    fontcolor = this.inverse_color(bgcolor)
                    style = style + 'background-color: ' + bgcolor + ';' + 'color: ' + fontcolor + ';';
                }
                    
            }
            return style
        }
    });
};