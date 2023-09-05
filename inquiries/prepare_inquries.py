"""


"""
import csv
import os
import random
import sqlite3
import time

import requests
import textract

try:
    os.mkdir("submissions")
except FileExistsError:
    pass


def extract_text_from_submission_file(submission_path):
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
        text,
        primary key (inquiry_shortname, submission_id)
    );

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


# Need to use a session to keep cookies
headers = {"From": "s.hames@uq.edu.au"}

session = requests.Session()
session.headers = headers


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

                db.execute(
                    "insert into submission values(:inquiry_shortname, :id, :submission_url, :filepath, :submitter, :text)",
                    submission,
                )

        db.execute("commit")
