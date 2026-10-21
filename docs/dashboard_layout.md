# Dashboard layout (first version)

Owner: Zahra. Code: `frontend/src/App.jsx` and `frontend/src/App.css`.

## Structure
- Header: product name and one-line purpose.
- Left navigation: five sections. Only the selected section is shown on the right.
- Main panel: the content of the selected section.
- On narrow screens (700 px or less) the navigation moves above the main panel.

## Sections
| # | Section | What it will show | Built |
|---|---|---|---|
| 1 | Upload data | Choose a CSV, see errors, warnings and a preview | Day 5 |
| 2 | Data summary | Customer counts, offered vs not offered, purchase rate | Later |
| 3 | Discount effects | Estimated effect of the discount per customer group | Later |
| 4 | Budget plan | Which customers to offer the discount to, given a budget | Later |
| 5 | Validation | Checks that the estimates can be trusted | Later |

## Rules
- Plain English; no code names except column names.
- Colour is always paired with an icon and a word.
- Every control can be used with the keyboard.