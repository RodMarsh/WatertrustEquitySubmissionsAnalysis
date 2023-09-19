"""
Prepare all inquiries using the inquiry header files.

This script downloads all available files (if not already downloaded), then
extracts the text from each file and saves it with appropriate metadata into
a relational SQLite database.

The moral foundations calculation is based on the following paper and
scoring implementation:

Hopp, F.R., Fisher, J.T., Cornell, D. et al. The extended Moral Foundations
Dictionary (eMFD): Development and applications of a crowd-sourced approach
to extracting moral intuitions from text. Behav Res 53, 232–246
(2021). https://doi.org/10.3758/s13428-020-01433-0

https://github.com/medianeuroscience/emfdscore


Not that the EMFD library doesn't have fully specified dependencies, you will
need to run the following first before anything will work:

pip install spacy scikit-learn
python -m spacy download en_core_web_sm
pip install git+https://github.com/medianeuroscience/emfdscore.git

"""

import csv
import os
import random
import sqlite3
import time

from emfdscore import scoring
import requests
import spacy
import textract

try:
    os.mkdir("submissions")
except FileExistsError:
    pass


db = sqlite3.connect("inquiries.db", isolation_level=None)

db.executescript(
    """
    drop table if exists inquiry;
    create table inquiry (
        inquiry_shortname text primary key,
        name
    );

    drop table if exists submission;
    create table submission (
        inquiry_shortname references inquiry,
        submission_id,
        url,
        filepath,
        submitter,
        submitter_normalised,
        text,
        primary key (inquiry_shortname, submission_id)
    );

    drop table if exists submission_emfd_score;
    create table submission_emfd_score (
        inquiry_shortname references inquiry,
        submission_id,
        score_type text,
        score float,
        primary key (inquiry_shortname, submission_id, score_type),
        foreign key (inquiry_shortname, submission_id) references submission
    )

    """
)


def extract_text_from_file(submission_file, file_format):
    """Extract plaintext from the given submission file."""

    if file_format == "pdf":
        text = textract.process(submission_file).decode("utf8")
    elif file_format == "skip":
        text = ""
    else:
        raise TypeError("Not a supported file_format")

    return text


def normalise_submitter(submitter):
    """
    Remove common honorifics from submitters for comparison across inquiries.

    """
    submitter = submitter.strip()

    # Test longest honorifics first to avoid partial matches. For example
    # 'Mr & Mrs' needs to be tested before 'Mr', otherwise we end up with
    # '& Mrs'. Note that common honorifics are removed, but displayed against
    # the original name to avoid any confusion.
    honorifics = sorted(
        (
            "Mr & Mrs ",
            "Mr ",
            "Miss ",
            "Dr ",
            "mr ",
            "Prof ",
            "Prof. ",
            "Professor",
            "Ms ",
            "Mrs ",
            "Mrs & Mr ",
            "Mr and Mrs ",
            "Mr & Ms ",
            "Cr ",
            "Hon ",
            "Associate Professor",
        ),
        reverse=True,
        key=lambda x: len(x),
    )
    for honorific in honorifics:
        if submitter.startswith(honorific):
            return submitter[len(honorific) :].strip()

    return submitter


# Note this is inferred from the emfd code - as written it errors with current
# versions of spacy, so there might have been some drift or change over
# time.
nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])
# Can safely increase the default to accomodate the longer submissions -
# spacy warns about significant memory usage in the ner and parser components
# which we've already disabled.
nlp.max_length = 2000000


def score_emfd(text):
    doc = nlp(text)
    tokens = scoring.tokenizer(doc)
    return scoring.score_emfd_all_sent(tokens)


session = requests.Session()


with open("inquiries.csv", "r") as inquiries_file:
    inquiries = csv.DictReader(inquiries_file, quoting=csv.QUOTE_ALL)

    for inquiry in inquiries:
        shortname = inquiry["inquiry_shortname"]
        submissions_path = inquiry["submission_reference_file"]

        # make sure the submission specific file exists.
        try:
            os.mkdir(os.path.join("submissions", shortname))
        except FileExistsError:
            pass

        print(f"Processing {shortname=}")
        db.execute("begin")
        db.execute("insert into inquiry values(:inquiry_shortname, :name)", inquiry)

        with open(submissions_path, "r") as submissions_header:
            submissions = csv.DictReader(submissions_header, quoting=csv.QUOTE_ALL)

            for submission in submissions:
                submission_id = submission["id"]
                submission_format = submission["format"]
                download_to = os.path.join(
                    "submissions", shortname, f"{submission_id}.{submission_format}"
                )
                temp = download_to + ".temp"

                # Any submission with a URL is consider
                public_submission = bool(submission["submission_url"])

                # Download if a link is present and the file is not already present.
                if (
                    not os.path.exists(download_to)
                    and public_submission
                    and submission_format != "skip"
                ):
                    r = session.get(submission["submission_url"], allow_redirects=True)

                    # Make sure to actually check the status code, not
                    # just write a forbidden response to the output.
                    r.raise_for_status()
                    with open(temp, "wb") as temp_file:
                        temp_file.write(r.content)

                    os.rename(temp, download_to)
                    # Wait at least 2 seconds, and on average 10 seconds with
                    # some jitter.
                    time.sleep(2 + random.random() * 16)

                # Extract text from the submission and stuff in the database
                if public_submission:
                    text = extract_text_from_file(download_to, submission_format)
                else:
                    text = ""

                submission["inquiry_shortname"] = shortname
                submission["text"] = text
                submission["filepath"] = download_to
                submission["submitter_normalised"] = normalise_submitter(
                    submission["submitter"]
                )

                db.execute(
                    "insert into submission values(:inquiry_shortname, :id, :submission_url, :filepath, :submitter, :submitter_normalised, :text)",
                    submission,
                )

                # Apply EMFD score:
                scores = score_emfd(text)

                for score_type, score in scores.items():
                    submission["score_type"] = score_type
                    submission["score"] = score
                    db.execute(
                        "insert into submission_emfd_score values(:inquiry_shortname, :id, :score_type, :score)",
                        submission,
                    )

        db.execute("commit")


with open("submitter_labels.csv", "w") as f:
    writer = csv.writer(f, quoting=csv.QUOTE_ALL, dialect="excel")
    writer.writerow(
        [
            "inquiry_shortname",
            "submission_id",
            "filepath",
            "url",
            "submitter",
            "submitter_normalised",
        ]
    )

    # Make the CSV file for submitter annotation
    rows = db.execute(
        """
        select
            inquiry_shortname,
            submission_id,
            filepath,
            url,
            submitter,
            submitter_normalised
        from submission
        order by submitter_normalised
        """
    )

    for row in rows:
        writer.writerow(row)
