1. Accepted file type

The upload page should accept CSV files (.csv) only. If a user selects a PDF, Excel file, image, or another unsupported file type, the page should reject it and display:

“Unsupported file type. Please upload a CSV file.”

2. Required columns

The CSV must contain all 13 columns in our approved dataset schema:

customer_id
age
tenure_months
past_purchases_12m
avg_order_value_past
days_since_last_purchase
email_engagement
is_loyalty_member
region
discount_offered
purchased
order_value
discount_cost

The application should check for all required columns before analysis. It should also validate data types, missing values, valid ranges, and whether both treatment groups are present.

3. CSV preview

After a valid file is selected, the page should display:

The first 10 rows in a table.
The total number of rows and columns.
The column names and detected data types.
A validation summary showing any problems.
The number of treated customers (discount_offered = 1) and untreated customers (discount_offered = 0).

The user should be able to review the data before starting the analysis.

4. Error messages

Missing required columns

“Some required columns are missing. Please check your CSV against the required dataset schema.”

Empty file

“This CSV file is empty. Please upload a file containing customer records.”

Text in a numeric column

“Some columns contain invalid data. Please check that numeric fields contain valid numbers and that binary fields contain only 0 or 1.”

Only treated or only untreated customers

“This dataset must contain both treated and untreated customers. Please upload data containing records with discount_offered = 1 and discount_offered = 0.”

Invalid or missing values

“Your dataset contains missing or invalid values. Please review the validation report and correct the data before analysis.”

5. Success message

“CSV uploaded and validated successfully. Review your data preview, then start the causal analysis.”

6. Important validation rules
discount_offered and purchased must contain only 0 or 1.
age must be between 18 and 75.
tenure_months must be between 0 and 120.
email_engagement must be between 0 and 1.
region must contain an allowed region or trigger a clear validation warning.
customer_id must not be used as a predictive feature.
The observed upload must not require ground-truth columns such as p_no_discount, p_discount, or true_effect.
The application must explain validation errors instead of silently changing or guessing the data.
7. User experience

The page should provide clear loading and error states, allow users to replace an uploaded file, and prevent analysis from starting until the required validation checks pass. The layout should be responsive and easy for a beginner to understand.