### Excel File Requirements

- File must be in `.xlsx` format.
- Must contain a column with employee identifiers (e.g., VAT/ID/Passport).
- Data columns must match those defined in the selected mapping.
- Format has to be:

| VAT/ID/Passport | Base Salary | Extra Hours | Other Concepts.. |
|-----------------|-------------|-------------|------------------|
| 1               | 2000        | 500         | ...              |
| 2               | 1800        | 250         | ...              |

### Employee Requirements

In order to correctly match payroll entries with existing employees (and their linked partners), each employee must have a unique identifier set in one of the following fields:

- **Identification Nº** (`identification_id`)
- **Passport** (`passport_id`)

These fields must match the values provided in the corresponding Excel column. If no matching employee is found, the system will list the missing identifiers, and you will need to create the missing records or update the identifiers accordingly.

### Creating a Column Mapping

1. Navigate to **Accounting > Configuration > Payroll Mapping**.
2. Create a new mapping and configure:
   - Mapping name.
   - Target journal.
   - Name of the column containing employee VAT/ID/Pasport.
   - Mapping lines: Excel column → account → move type (debit/credit).
   Ex:
    "NET SALARY", 230000, credit

3. Save the mapping for future use.

### Import

1. Go to **Accounting > Accounting > Payroll Import**.
2. Upload an Excel file containing payroll data.
3. Choose a previously configured column mapping.
4. The system will attempt to match employees using VAT/ID/Passport numbers:
5. After validation, click **Import** to generate journal entries.
6. If employees are missing, a warning will show the unmatched identifiers.
