# -*- coding: utf-8 -*-
<html>
<head>
    <style type="text/css">

    table {
       width: 100%;
       page-break-after:auto;
       border-collapse: collapse;
       cellspacing="0";
       font-size:14px;
           }
    td { margin: 0px; padding: 3px; border: 1px solid lightgrey;  vertical-align: top; }
    .valign_up1, .valign_up2, .halign, .vtrait1, .vtrait2{
            position:absolute;
        }
    .valign_up1 { left:200px; font-weight: lighter; color:MediumSlateBlue ;
        }
    .valign_up2 { left:650px; font-weight: lighter; color:MediumSlateBlue ;
        }
    .halign { left:500px}
    .vtrait1 { left:185px; font-weight: lighter; color:MediumSlateBlue ; }
    .vtrait2 { left:630px; font-weight: lighter; color:MediumSlateBlue ; }
    .entete_tab {text-align:center; white-space:nowrap; border-bottom:1px solid;}
    .cellule_tab {white-space:nowrap; text-align:center;}
    .amount {white-space:nowrap; text-align:right;}
    .total {border-top:2px solid;}
    .titre {text-align:center; font-family:helvetica; font-size:35px; background:lightgrey}

    pre {font-family:helvetica; font-size:12px;}
    h1 {font-family:helvetica; font-size:18px;}
    h2 {font-family:helvetica; font-size:25px; border-bottom:1px solid}
    h3 {font-family:helvetica; font-size:22px; color: MediumSlateBlue   ; margin-bottom: auto;}


    </style>
</head>
<body>
%for deposit in objects :
<% setLang(deposit.company_id.partner_id.lang) %>
<b><span class="titre">${_("Deposit Slip of Checks in ")} ${deposit.currency_id.name}</span></b>

<table class="basic_table" width="100%">
    <tr>
        <th class="date">${_("Deposit Date")}</th>
        <th class="text-align:center;">${_("Deposit Ref")}</th>
        <th class="text-align:center;">${_("Beneficiary")}</th>
        <th class="text-align:center;">${_("Bank Account Number")}</th>
    </tr>
    <tr>
        <td class="date">${formatLang(deposit.deposit_date, date=True)}</td>
        <td class="text-align:center;">${deposit.name}</td>
        <td class="text-align:center;">${deposit.company_id.partner_id.name}</td>
        <td class="text-align:center;">${deposit.partner_bank_id.acc_number}</td>
    </tr>
</table>

<h3>${_("Check Payments")}</h3>

    <table style="width:100%">
        <thead>
          <tr>
<th class="entete_tab">${_("Payment Date")}</th>
<th class="entete_tab">${_("Reference")}</th>
<th class="entete_tab">${_("Debtor")}</th>
<th class="entete_tab">${_("Amount")}</th>
        </thead>
          </tr>

     %for move_line in deposit.check_payment_ids :
    <tbody>
        <tr>
        <td class="cellule_tab">${move_line.date or ''}</td>
        <td class="cellule_tab">${move_line.ref or ''}</td>
        <td class="cellule_tab">${move_line.partner_id.name or ''}</td>
        <td class="amount">${deposit.currency_id == deposit.company_id.currency_id and move_line.debit or move_line.amount_currency} ${deposit.currency_id.name}</td>
        </tr>
    </tbody>
    %endfor
    %endfor
    <tfoot>
            <tr>
                <td colspan="3" class="amount total"><b>${_("Total:")}</b></td>
                <td class="amount total"><b>${deposit.total_amount or '0'} ${deposit.currency_id.name}</b></td>
            </tr>
        </tfoot>
     </table>

</body>
</html>
