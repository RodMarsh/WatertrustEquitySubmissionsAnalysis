# Text analytics for examining Equity, Fairness and Justice

This project examines the text of various sources to examine claims and
considerations of equity, fairness and justice in Water Policy in Australia.

## Structure and Key Files/Folders

### Data/Folders

- `inquiries/` - holds all inquiry related raw data and associated data collection scripts
- `inquiries/inquiries.csv` - the header file describing all inquiries analysed, one row per inquiry
- `inquiries/<inquiry_shortname>.csv` - One file per inquiry, one row per submission in that inquiry, including details of the submission file, submitter etc.
- `inquiries/submissions` - download location of submission files (not for further distribution)
- `inquiries/per_inquiry_wrangling` - One off scripts and reference data used to produce the individual inquiry submission indexes as described in `inquiries/<inquiry_shortname>.csv`
- `inquiries/inquiries.db` - the database file generated after processing all metadata and extracting all text.


### Scripts

- `inquiries/prepare_inquiries.py` - the main script for downloading and preparing data. This script is driven by `inquiries/inquiries.csv` and the associated `inquiries/<inquiry_shortname>.csv` files.
- `inquiries/per_inquiry_wrangling/<inquiry_shortname>.py` - any per inquiry data manipulation necessary to generate the relevant index file.

