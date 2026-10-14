# Account Journal Creation from Chart of Accounts

To use this module, follow these steps:

1. Go to **Accounting > Configuration > Chart of Accounts**.
2. Select one or multiple accounts of type **Bank**.
3. Click the **Create Journal** button from the list view  
   or use the **Action > Create Journal** server action.
4. If a journal does not exist, a new journal will be created automatically.
5. If a journal already exists for the selected account:
   - A confirmation wizard will appear.
   - Click **Yes** to create a new journal again, or **Cancel** to stop.
6. Once created, the journal will:
   - Be of type **Bank** based on the account type.
   - Automatically configure **Incoming Payments** and **Outgoing Payments** if:
     - **Inbound Payment Account** and **Outbound Payment Account** are set in Accounting Settings.
7. Open the created journal from the **Accounting > Configuration > Journals** menu for further use.
