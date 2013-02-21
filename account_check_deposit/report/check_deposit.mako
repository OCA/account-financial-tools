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
<% setLang(deposit.partner_id.lang) %>
<b><span class="titre">${_("Deposit Slip of Checks(Euros)")}</span></b>
<br>
<br>
<br>
<br>
<br>
<br>
        <h2>
<b>${_("Deposit N°")} ${deposit.name}</b>
        </h2>

        <h1>
<b>${_("Deposit Date")}</b><span class="vtrait1">${_("|")}</span>
<span class="valign_up1"> ${deposit.deposit_date}</span>
<b><span class="halign">${_("Bank Code")}</span></b>
<span class="vtrait2">${_("|")}</span><span class="valign_up2"> ${deposit.bank_id.bank_code}</span>
<br>
<b>${_("Beneficiary")}</b><span class="vtrait1">${_("|")}</span>
<span class="valign_up1"> ${company.partner_id.name}</span>
<b><span class="halign">${_("Office Code")}</span></b>
<span class="vtrait2">${_("|")}</span><span class="valign_up2"> ${deposit.bank_id.office}</span>
<br>
<b>${_("Account to crediting")}</b><span class="vtrait1">${_("|")}</span>
<span class="valign_up1"> ${deposit.bank_id.rib_acc_number}</span>
<b><span class="halign">${_("BIS Key")}</span></b><span class="vtrait2">${_("|")}</span>
<span class="valign_up2"> ${deposit.bank_id.key}</span>
        </h1>
<br>
        <h3>
<b>${_("Check Payments")}</b>
        </h3>

    <table style="width:100%">
        <thead>
          <tr>
<th class="entete_tab">${_("Payment Date")}</th>
<th class="entete_tab">${_("Reference")}</th>
<th class="entete_tab">${_("Description")}</th>
<th class="entete_tab">${_("Designation")}</th>
<th class="entete_tab">${_("Amount")}</th>
        </thead>
          </tr>

<br>
     %for move_line in deposit.check_payment_ids :
    <tbody>
        <tr>
        <td class="cellule_tab">${move_line.date or ''}</td>
        <td class="cellule_tab">${move_line.ref or ''}</td>
        <td class="cellule_tab">${move_line.name or ''}</td>
        <td class="cellule_tab">${move_line.partner_id.name or ''}</td>
        <td class="amount">${move_line.debit or '0'}</td>
        </tr>
    </tbody>
    %endfor
    %endfor
    <tfoot>
            <tr>
                <td colspan=4 class="amount total"><b>${_("Total:")}</b></td>
                <td colspan=5 class="amount total"><b>${deposit.total_amount or '0'}</b></td>
            </tr>
        </tfoot>
     </table>







</body>
</html>
