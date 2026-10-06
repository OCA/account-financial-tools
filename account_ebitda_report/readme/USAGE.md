To use this module, you need to:

1.  Go to *Accounting \> Reporting \> MIS Reporting \> MIS Reports*.
2.  Select one of the available templates:
    - **EBITDA (Bottom-up)**: Simple approach starting from Net Profit.
    - **EBITDA (Top-down)**: Simple approach starting from Operating
      Revenue.
    - **EBITDA (Professional & Adjusted)**: Advanced M&A ready report
      with Margins, Debt Ratios, and Free Cash Flow bridge.
3.  Configure the column periods. For advanced usage, you can configure:
    - **TTM (Trailing Twelve Months)**: Create a column of type
      "Relative to current period", Duration "-12 months".
    - **Run-Rate**: Configure a custom period column.
    - **Analytic Dimensions**: Use the analytic filters in the MIS
      Report instance to hyper-segment the EBITDA by Business Line, Cost
      Center, or Project.
4.  For precise mapping (if you are not using a localization extension
    like l10n_es_ebitda), go to your Chart of Accounts and assign the
    provided EBITDA / \* tags to your accounts.

**M&A Normalization Examples:**

- If the owner's salary is above market rate by 50,000€, tag the
  corresponding accounting entry or account with EBITDA / M&A Adj: Owner
  Salary. The Professional report will automatically add it back to the
  Adjusted EBITDA.
- Track Fixed Asset purchases (CAPEX) by tagging the Asset accounts
  (e.g., machinery) with EBITDA / CAPEX (Fixed Asset Additions).
