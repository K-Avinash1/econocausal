# Upload feedback: what the user sees

Owner: Zahra. Based on `docs/validation_messages.md`, which lists the messages the backend
validator really produces for each file in `data/samples/`.

## 1. Rules for every message
1. Say what is wrong, where it is (which column), and how to fix it.
2. Use plain English. No code names except column names, which the user must match exactly.
3. Never rely on colour alone. Every message has an icon and a word: "Error", "Warning" or "Success".
4. Never claim success unless the backend has actually accepted the file.

## 2. The three outcomes

| Outcome | Colour and label | "Run analysis" button | Preview table |
|---|---|---|---|
| Error | Red, "Error" | Disabled | Shown if the rows could be read; hidden for an empty file |
| Warning | Amber, "Warning" | Enabled | Shown |
| Success | Green, "Success" | Enabled | Shown |

## 3. Messages for each sample file

| Sample file | What is wrong | Outcome | Message shown to the user | Page behaviour |
|---|---|---|---|---|
| `sample_valid.csv` | Nothing | Success | File accepted. | Show customer count, share offered the discount, purchase rate, and the preview. Enable "Run analysis". |
| `warning_500_rows.csv` | Only 500 rows | Warning | The file has 500 rows. Results will be noisy; 1000+ customers are recommended. | Show the amber warning above the preview. Enable "Run analysis". |
| `invalid_missing_columns.csv` | Two required columns are absent | Error | These required columns are missing: region, discount_offered. Column names must match exactly (for example 'discount_offered'). | Red message. Preview shows the columns that were found. Disable "Run analysis". |
| `invalid_text_in_number.csv` | Words in a numeric column | Error | Column 'age' must contain numbers only, but 3 value(s) are text (for example forty). | Red message. Disable "Run analysis". |
| `invalid_all_treated.csv` | Everyone was offered the discount | Error | In column 'discount_offered', every customer was offered the discount. The effect of a discount cannot be measured without both treated and untreated customers. | Red message. Disable "Run analysis". |
| `invalid_none_treated.csv` | Nobody was offered the discount | Error | In column 'discount_offered', no customer was offered the discount. The effect of a discount cannot be measured without both treated and untreated customers. | Red message. Disable "Run analysis". |
| `invalid_empty.csv` | Header only, no customers | Error | The file has no data rows. Upload a CSV that contains customer rows under the header. | Red message. No preview. Disable "Run analysis". |
| `invalid_too_few_rows.csv` | Only 50 rows | Error (two messages) | The file has only 50 rows. At least 200 customers are needed to estimate discount effects. / Only 19 customers are in the smaller group (offered vs not offered). At least 50 are needed in each group. | Show both messages as a list. Disable "Run analysis". |
| `invalid_bad_region.csv` | A region that is not allowed | Error | Column 'region' contains values that are not allowed (Central). Allowed: North, South, East, West. | Red message. Disable "Run analysis". |
| `invalid_duplicate_ids.csv` | The same customer appears twice | Error | Column 'customer_id' has 1 duplicate ID(s). Each customer must appear once. | Red message. Disable "Run analysis". |
| `invalid_missing_values.csv` | Empty cells | Error | Column 'email_engagement' has 2 empty value(s). Fill or remove those rows. | Red message. Disable "Run analysis". |
| `invalid_not_binary.csv` | A yes/no column has a 2 | Error | Column 'is_loyalty_member' must contain only 0 or 1, but found 2. | Red message. Disable "Run analysis". |

## 4. Messages written by the page itself (before the backend is asked)

| Situation | Message |
|---|---|
| The chosen file is not a .csv | Please choose a CSV file (a file whose name ends in .csv). |
| The file is larger than 10 MB (proposed limit, approved by Avinash) | This file is larger than 10 MB. Please upload a smaller file. |
| The file cannot be read as a CSV | We could not read this file as a CSV. Check that the values are separated by commas. |
| The backend is not running (from Day 6) | We could not reach the analysis server. Check that the backend is running and try again. |

## 5. Several errors at once
Show every error as its own line in one red box. If there are more than 5, show the first 5 and
add "and N more". Finish with: "Fix these problems and upload the file again."

## 6. The success view
- Heading: "File accepted".
- Summary line: number of customers, percentage offered the discount, percentage who purchased.
  These numbers come from the validator summary (`n_rows`, `treated_share`, `purchase_rate`).
- Preview: the first 10 rows in a table that scrolls sideways on narrow screens.
- Any warnings appear in amber above the preview.
- Button: "Run analysis".

## 7. Accessibility
- The file chooser has a visible label: "Choose a CSV file".
- Error messages sit in an element with `role="alert"` so screen readers announce them.
- Colour is always paired with an icon and a word.

## 8. Open questions for Avinash
- Is 10 MB the right maximum file size? (20,000 customers is about 1 MB.)
- Should a warning ask the user to confirm before "Run analysis"?