# Clean-start test (Day 7)

Tester: Zahra. Date: 21 Oct 2026
Computer: Windows 11, Python 3.13.0, Node v24.21.0, npm 11.19.0
Fresh clone of `main`, commit id: 849caea

## Steps
| # | Step | Expected | Result (PASS/FAIL) | Notes |
|---|---|---|---|---|
| 1 | Clone and look at the folder | README.md, backend, data, docs, frontend, scripts are present | PASS | Commit id matched main (849caea). |
| 2 | README "Light install" | no errors | PASS | The commands were hard to find (see Problems). |
| 3 | README "Run the backend API", open /health | `{"status":"ok","service":"econocausal","version":"0.1.0"}` | PASS | |
| 4 | README "Run the frontend", open http://localhost:5173 | dashboard with 5 sections | PASS | |
| 5 | Upload `sample_valid.csv` | green "File accepted", 1,000 customers | PASS | |
| 6 | `python scripts/smoke_test_api.py` | `20 passed, 0 failed` | PASS | Output: 20 passed, 0 failed. |

## The 12 sample files on the page
| File | Page showed the message in docs/upload_feedback.md? (yes/no) | Notes |
|---|---|---|
| sample_valid.csv | yes | |
| warning_500_rows.csv | yes | Amber warning and green "File accepted" both shown. |
| invalid_missing_columns.csv | yes | |
| invalid_text_in_number.csv | yes | |
| invalid_all_treated.csv | yes | |
| invalid_none_treated.csv | yes | |
| invalid_empty.csv | yes | No preview table, as expected. |
| invalid_too_few_rows.csv | yes | Two messages shown. |
| invalid_bad_region.csv | yes | |
| invalid_duplicate_ids.csv | yes | |
| invalid_missing_values.csv | yes | |
| invalid_not_binary.csv | yes | |

## Problems with the README or setup instructions
- README, section "Backend setup": the "Light install (frontend work only, no model libraries)" commands are a small sub-heading under "Backend setup" and were hard to find for someone who only works on the frontend. Suggestion: add a short "Quick start for the upload page" section near the top of the README that lists the three light-install commands, the backend command and the frontend command in order.