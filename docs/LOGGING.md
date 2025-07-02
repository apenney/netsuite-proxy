# Logging

There's a lot of potential fields that make sense when logging. For each case of
this providing useful, we want to standardize the field in json. Here are some
fields you can use when appropriate.

1. Customer/Vendor Context

- customer_id / customer_ids - Essential for tracking customer-related operations
- vendor_id - For vendor operations
- company_id - Used in contact creation
- subsidiary_id - Important for multi-subsidiary accounts

2. Transaction Identifiers

- invoice_id - Invoice operations
- bill_id / bill_ids - Vendor bill operations
- record_id with record_type - Generic record references
- external_id - External system references
