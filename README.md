# Spreadsheet Contact Cleaner

A Python automation tool that cleans messy contact spreadsheets and produces:
- a cleaned CSV output
- a summary cleaning report

## Problem
Businesses often store contacts in spreadsheets with inconsistent formatting, duplicates, and invalid data.
This makes emailing, CRM imports, and reporting unreliable.

## Solution
This script:
- trims and normalises text fields
- standardises names, emails, companies, and UK phone numbers
- validates emails/phones and reports issues
- removes duplicates (by email) while keeping the best record
- outputs a cleaned CSV + a report file

## Input
`data/contacts_raw.csv`

## Output
- `output/cleaned_contacts.csv`
- `output/cleaning_report.txt`

## How to run
```bash
python main.py
