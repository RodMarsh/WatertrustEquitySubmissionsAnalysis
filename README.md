# Text analytics for examining Equity, Fairness and Justice

This project examines the text of various sources to examine claims and
considerations of equity, fairness and justice in Water Policy in Australia.

## Data Preparation

Data from inquiries is downloaded, the text extracted and inserted into a
single SQLite database - this is intended to provide a single datasource for
all downstream analysis (regardless of how the analysis is done).

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
python -m pip install lxml pytesseract pymupdf requests

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
- `inquiries/per_inquiry_wrangling/<inquiry_shortname>.py` - any per inquiry data manipulation necessary to generate the relevant index file. This is included for documentation purposes, and do not need to be run for existing files: the inquiry specific CSV file is the version of record for driving data downloads.


### OCR and format handling

Almost all submissions are in PDF format already. However, not all submissions are necessarily in a nice digital format for easy text extraction. Submissions can be one of the following types, and go through a different processing pipeline depending on the annotated format in the inquiry submissions file located at `inquiries/<inquiry_shortname>.csv`.

- `pdf`: The text of the PDF will be extracted as is. Note that some scanned documents have already had an OCR layer added, the `pdf` format can be used for those using the embedded OCR.
- `pdf-ocr`: The images in the PDF will be extracted and run through tesseract via pytesseract to recognise the text content. This is appropriate for typeset document that have been scanned - tesseract is set to automatically choose the right script and orientation, and it appears that all submissions are in English, or mostly English.
- `pdf-mixed`: The document contains a mixture of both digital and scanned typeset material: for this both the text will be extracted and OCR applied. This shouldn't be used for documents with their own OCR embedded, otherwise there will be a doubling of the text. 
- `pdf-handwritten`: The document is completely handwritten, and OCR with tesseract will not work, or there is a mixture of typeset and handwritten material that is difficult to untangle. This format type requires manual transcription.
- `txt`: A plain text file that will be read as is.


## Analysis

All analysis code is in R notebooks in the `analysis` folder. They all assume that the data is read from the `inquiries/inquiries.db` SQLite database and that the `inquiries/prepare_inquiries.py` has been run.

The main analyses are conducted in the following files:

- `analysis/01_submission_summary.Rmd`
- `analysis/02_keyword_selected_concordance.Rmd`
- `analysis/04_sensitivity.Rmd`


## Adding a New Inquiry

Adding a new inquiry requires generating a CSV file describing the submitter details, the location to download the submitter files from, and the format of the submission for the purposes of extracting the text from the document. Then the header CSV `inquiries/inquiries.csv` describing all the included inquiries needs to be edited to add the row pointing to that new file. 

For examples of how to generate inquiries, the scripts for each included inquiry are in `inquiries/per_inquiry_wrangling/<inquiry_shortname>.py` - in general this requires pulling apart the specific structure of the page for the inquiry listing all the submissions: limited automation is possible for this step.


## Copyright Notes

The actual text and files of the submissions (apart from Hansard) are generally the copyright of the original submitter and we do not have permission to redistribute them. For this reason we only include the code and pipeline to redownload the submissions yourself and not the actual data.
