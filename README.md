# Text analytics for examining Equity, Fairness and Justice

This project examines the text of various sources to examine claims and
considerations of equity, fairness and justice in Water Policy in Australia.

## Data Preparation

Data from inquiries is downloaded, the text extracted and inserted into a single SQLite database - this is intended to provide a single datasource for all downstream analysis (regardless of how the analysis is done).

### Dependencies and Setup

You'll need [Python installed](https://www.python.org/downloads/) on your machine.

It's better to run this in a virtual environment - using the command line you can download and prepare all the data here: 

```
# Assuming you have changed directory to the root of this repository
python -m venv inquiry_data

# Activate the virtual environment (Windows)
inquiry_data\Scripts\activate.bat
# OR not windows
source inquiry_data/bin/activate

# Install dependencies
python -m pip install lxml textract requests

# Run the data preparation script
cd inquiries
python prepare_inquiries.py

```


### Data and Key Files and Folders

- `inquiries/` - holds all inquiry related raw data and associated data collection scripts
- `inquiries/inquiries.csv` - the header file describing all inquiries analysed, one row per inquiry
- `inquiries/<inquiry_shortname>.csv` - One file per inquiry, one row per submission in that inquiry, including details of the submission file, submitter etc.
- `inquiries/submissions` - download location of submission files (not for further distribution)
- `inquiries/per_inquiry_wrangling` - One off scripts and reference data used to produce the individual inquiry submission indexes as described in `inquiries/<inquiry_shortname>.csv`
- `inquiries/inquiries.db` - the database file generated after processing all metadata and extracting all text.


### Scripts

- `inquiries/prepare_inquiries.py` - the main script for downloading and preparing data. This script is driven by `inquiries/inquiries.csv` and the associated `inquiries/<inquiry_shortname>.csv` files.
- `inquiries/per_inquiry_wrangling/<inquiry_shortname>.py` - any per inquiry data manipulation necessary to generate the relevant index file.

