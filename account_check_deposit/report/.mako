<html>
<head>
    <style type="text/css">
        ${css}
        pre {font-family:helvetica; font-size:12;}
    </style>
</head>
<body>
    <style  type="text/css">
     table {
       width: 100%;
       page-break-after:auto;
       border-collapse: collapse;
       cellspacing="0";
       font-size:10px;
           }
     td { margin: 0px; padding: 3px; border: 1px solid lightgrey;  vertical-align: top; }
     pre {font-family:helvetica; font-size:12;}
    </style>

    <%
    def carriage_returns(text):
        return text.replace('\n', '<br />')
    %>

    %for order in objects :
<br>
    <% setLang(order.partner_id.lang) %>
    <table >
        %if order.company_id.address_label_position == 'left':
         <tr>
         <td style="width:50%">
${_("Shipping Address")}   
<hr>
           <pre>
${order.partner_shipping_id.address_label}
           <pre>
         </td>
         <td style="width:50%">
         %if order.partner_id.address_label != order.partner_shipping_id.address_label:
<b>${_("Ordering Contact")}</b><br>
${order.partner_id.address_label|carriage_returns}
         %endif
         %if order.partner_id.phone :
${_("Phone")}: ${order.partner_id.phone|entity} <br>
        %endif
        %if order.partner_id.fax :
${_("Fax")}: ${order.partner_id.fax|entity} <br>
        %endif
        %if order.partner_id.email :
${_("Mail")}: ${order.partner_id.email|entity} <br>
        %endif
         %if order.partner_invoice_id.address_label != order.partner_shipping_id.address_label:
<br>
<b>${_("Invoice Address")}</b><br>
${order.partner_invoice_id.address_label|carriage_returns}
         %endif
        %if order.partner_invoice_id.partner_id.vat :
${_("VAT")}: ${order.partner_invoice_id.partner_id.vat|entity} <br>
        %endif
   
         </td>

        </tr>
        %endif

        %if order.company_id.address_label_position == 'right' or not order.company_id.address_label_position:
         <tr>
         <td style="width:50%">
         %if order.partner_id.address_label != order.partner_shipping_id.address_label:
<b>${_("Ordering Contact")}</b><br>
<hr>
${order.partner_id.address_label|carriage_returns}
        %endif
         %if order.partner_id.phone :
${_("Tel")}: ${order.partner_id.phone|entity} <br>
        %endif
        %if order.partner_id.fax :
${_("Fax")}: ${order.partner_id.fax|entity} <br>
        %endif
        %if order.partner_id.email :
${_("E-mail")}: ${order.partner_id.email|entity} <br>
        %endif
         %if order.partner_invoice_id.address_label != order.partner_shipping_id.address_label:
<br>
<hr>    
<b>${_("Invoice Address")}</b><br>
<hr>
${order.partner_invoice_id.address_label|carriage_returns}
         %endif
        %if order.partner_invoice_id.vat :
${_("VAT")}: ${order.partner_invoice_id.vat|entity} <br>
        %endif

         </td>
         <td style="width:50%">
<b>${_("Shipping Address")}</b><br>
<hr>
           <pre>
${order.partner_shipping_id.address_label}
           <pre>
         </td>
        </tr>
        %endif
    </table>

    <br />
    <br />

    %if order.state == 'draft' :
    <span class="title">${_("Quotation N°")} ${order.name or ''|entity}</span>
    %elif order.state == 'cancel' :
    <span class="title">${_("Sale Order Canceled")} ${order.name or ''|entity}</span>
    %else :
    <span class="title">${_("Order N°")} ${order.name or ''|entity}</span>
    %endif
    <br/>
    <table  style="width:100%">
        <tr>
          %if order.client_order_ref:
            <td>${_("Reference")}</td>
          %endif
          %if order.project_id:
            <td>${_("Projekt")}</td>
          %endif
            <td style="text-align:center;white-space:nowrap"><b>${_("Order Date")}</b></td>
          %if order.carrier_id:
            <td style="text-align:center;white-space:nowrap"><b>${_("Carrier")}</b></td>
          %endif
          %if order.user_id:
            <td style="text-align:center;white-space:nowrap"><b>${_("Salesman")}</b></td>
          %endif
          %if order.payment_term :
            <td style="text-align:center;white-space:nowrap"><b>${_("Payment Term")}</b></td>
          %endif
          %if order.incoterm:
             <td style="text-align:center;white-space:nowrap"><b>${_("Incoterm")}</b></td>
          %endif

            <td style="text-align:center;white-space:nowrap"><b>${_("Curr")}</b></td>
        </tr>
        <tr>
            %if order.client_order_ref:
            <td>
               ${order.client_order_ref}
            </td>
            %endif
          %if order.project_id:
            <td>${order.project_id.name}</td>
          %endif
            %if order.date_order:
             <td>
               ${order.date_order or ''}</td>
            %endif
            %if order.carrier_id:
             <td>
               ${order.carrier_id.name }
             </td>
           %endif
           %if order.user_id :
             <td>${order.user_id.name or ''}</td>
           %endif
          %if order.payment_term :
            <td>${order.payment_term.name}</td>
          %endif
          %if order.incoterm:
             <td>${order.incoterm.name}</td>
          %endif

            <td style="white-space:nowrap">${order.pricelist_id.currency_id.name} </td>
    </table>
    <h1><br /></h1>
    <table style="width:100%">
        <thead>
          <tr>
%if order.print_code:
            <td style="text-align:center;white-space:nowrap"><b>${_("Code")}</b></td>  
            <td style="text-align:center;white-space:nowrap"><b>${_("Description")}</b></td>
%else:
            <td style="text-align:center;white-space:nowrap"><b>${_("Description")}</b></td>
%endif
            <td style="text-align:center;white-space:nowrap"><b>${_("Tax")}</b></td>
%if order.print_uom:
            <td style="text-align:center;white-space:nowrap"><b>${_("Quantity")}</b></td><td style="text-align:center;white-space:nowrap"><b>${_("UoM")}</b></td>
%endif
%if order.print_uos:
            <th style="text-align:center;white-space:nowrap">${_("UoS Qty")}</th><th style="text-align:center;white-space:nowrap;">${_("UoS")}</th>
%endif
%if order.print_ean:
            <td style="text-align:center;white-space:nowrap"><b>${_("EAN")}</b></td>
%endif
%if order.print_packing:
            <td style="text-align:center;white-space:nowrap"><b>${_("Pack")}</b></td>
            <td style="text-align:center;white-space:nowrap"><b>${_("Packaging")}</b></td>
%endif
            <td style="text-align:center;white-space:nowrap"><b>${_("Price Unit")}</b></td>
%if order.print_discount:
            <td style="text-align:center;white-space:nowrap"><b>${_("Discount")}</b></td>
%endif
            <td style="text-align:center;white-space:nowrap"><b>${_("Sub Total")}</b></td>
         </tr>
        </thead>
        %for line in order.order_line_sorted :
        <tbody>
        <tr>
%if order.print_code:
            <td>${line.product_id.default_code or ''|entity}</td>
            <td>
${line.product_id.name or line.name|entity}
    
        
</td>
%else:
  <td>${line.name|entity}
        
 </td
%endif
           <td>${ ', '.join([tax.name or '' for tax in line.tax_id]) }</td>
%if order.print_uom:
           <td style="white-space:nowrap;text-align:right;">${str(line.product_uom_qty).replace(',000','') or '0'}</td>
           <td style="white-space:nowrap;text-align:left;">${line.product_uom.name or ''}</td>
%endif
%if order.print_uos:
           <td style="white-space:nowrap;text-align:right;">${str(line.product_uos_qty).replace(',000','') or '0'}</td>
           <td style="white-space:nowrap;text-align:left;">${line.product_uos.name or ''}</td>
%endif
%if order.print_ean:
           <td style="white-space:nowrap;text-align:left;">${line.product_packaging.ean or line.product_id.ean13 or ''}</td>
%endif
%if order.print_packing:
           <td style="white-space:normal;text-align:left;">${line.product_packaging.qty and line.product_uom_qty/line.product_packaging.qty or ''}</td>
           <td style="white-space:normal;text-align:left;">${line.product_packaging and line.product_packaging.ul.name or ''} ${line.product_packaging and _(" / " or '')} ${line.product_packaging and line.product_packaging.qty or ''} ${line.product_packaging and line.product_id.uom_id.name or ''}</td>
%endif
           <td style="white-space:nowrap;text-align:right;">${line.price_unit or ''}</td>
%if order.print_discount:
           <td style="text-align:right;">${line.discount}</th>
%endif
           <td style="white-space:nowrap;text-align:right;">${line.price_subtotal or ''}</td>
        </tr>
        %endfor
        </tbody>
        <tfoot>
            <tr>
                <td colspan="${order.cols}" style="border-style:none"/>
                <td style="border-top: 2px solid"><b>${_("Net Total:")}</b></td>
                <td class="amount"  style="border-top:2px solid;text-align:right;">${formatLang(order.amount_untaxed, get_digits(dp='Sale Price'))} </td>
            </tr>
            <tr>
                <td colspan="${order.cols}" style="border-style:none"/>
                <td style="border-style:none"><b>${_("Taxes:")}</b></td>
                <td class="amount" style="text-align:right;">${formatLang(order.amount_tax, get_digits(dp='Sale Price'))} </td>
            </tr>
            <tr>
                <td colspan="${order.cols}" style="border-style:none"/>
                <td style="border-top:2px solid"><b>${_("Total:")}</b></td>
                <td class="amount" style="border-top:2px solid;text-align:right;">${formatLang(order.amount_total, get_digits(dp='Sale Price'))} </td>
            </tr>
        </tfoot>

    </table>

%if order.note and 'note_print' not in order._columns:
<br>
    <pre>${order.note}</pre>
%endif:
%if 'note_print' in order._columns and order.note_print:
<br>
    <pre>${order.note_print}</pre>
%endif:


    <p style="page-break-after:always"></p>
    %endfor 
</body>
</html>
