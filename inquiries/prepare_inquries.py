"""
Prepare all inquiries using the inquiry header files.

This script downloads all available files (if not already downloaded), then
extracts the text from each file and saves it with appropriate metadata into
a relational SQLite database.

pip install requests pymupdf pytesseract

You will also need to install the tesseract OCR library - how to install
this depends on your OS. On Ubuntu the installation is:

sudo apt install tesseract-ocr

"""

import sys
import csv
import io
import os
import random
import re
import sqlite3
import time

import fitz
from PIL import Image
import pytesseract
import requests
import spacy

try:
    os.mkdir("submissions")
except FileExistsError:
    pass


def extract_text_from_file(
    submission_file, file_format, boilerplate_regex, page_start, page_end
):
    """
    Extract plaintext from the given submission file.

    Blocks of text that match the optional boilerplate_regex after stripping
    whitespace will not be included.

    """

    skipped = []

    if file_format in ("pdf", "pdf-mixed"):
        text_chunks = []
        with fitz.open(submission_file) as submission:
            for page_sequence, page in enumerate(submission):
                if not (page_start <= page_sequence <= page_end):
                    # Skip page numbers out of the specified range
                    print(
                        f"skipping page {page_sequence}, not between {page_start}, {page_end}"
                    )
                    continue
                for text in page.get_text("blocks", sort=True):
                    # Skip text associated with images
                    if text[4].startswith("<image: DeviceRGB"):
                        skipped.append(text[4])
                    # Skip inquiry specific boilerplate
                    elif boilerplate_regex and boilerplate_regex.match(text[4].strip()):
                        skipped.append(text[4])
                    else:
                        text_chunks.append(text[4].strip())

        text = " ".join(text_chunks)

    if file_format in ("pdf-ocr", "pdf-mixed"):
        text_chunks = []
        with fitz.open(submission_file) as submission:
            # An image can be included multiple times in a file, such as in a
            # header/footer - we only handle the first of these images.
            seen_images = set()
            for page_sequence, page in enumerate(submission):
                if not (page_start <= page_sequence <= page_end):
                    # Skip page numbers out of the specified range
                    print(
                        f"skipping page {page_sequence}, not between {page_start}, {page_end}"
                    )
                    continue

                for image in page.get_images():
                    # Skip duplicate images
                    if image[0] in seen_images:
                        continue

                    seen_images.add(image[0])
                    pixmap = fitz.Pixmap(submission, image[0])
                    try:
                        im_data = pixmap.tobytes("png")
                    except Exception:
                        try:
                            im_data = pixmap.pil_tobytes("png")
                        except Exception:
                            # The edge case here should be the CMYK images, which
                            # are only used in certain prepared for print
                            # submissions.
                            print(f"skipping unhandled pixmap {pixmap}")
                            continue

                    ocr_text = pytesseract.image_to_string(
                        # Handle indexed images conversion to png
                        Image.open(io.BytesIO(im_data)),
                        lang="eng",
                        # This mode is page auto segmentation with orientation
                        # and script detection - the default is page auto
                        # segmentation without the second two which can fail
                        # for some files.
                        config="--psm 1",
                    )
                    text_chunks.append(ocr_text)

        text = " ".join(text_chunks)
        # Need to be sure the OCR is actually working.
        print(submission_file, text)

    if file_format == "pdf-vector-ocr":
        # Some print to PDF options turn text into vectors drawn on the screen...
        # Handle these by rendering the whole page, then passing to tesseract.
        text_chunks = []
        with fitz.open(submission_file) as submission:
            for page_sequence, page in enumerate(submission):
                if not (page_start <= page_sequence <= page_end):
                    # Skip page numbers out of the specified range
                    print(
                        f"skipping page {page_sequence}, not between {page_start}, {page_end}"
                    )
                    continue

                pixmap = page.get_pixmap(dpi=300)

                ocr_text = pytesseract.image_to_string(
                    Image.open(io.BytesIO(pixmap.tobytes("png"))),
                    lang="eng",
                    # This mode is page auto segmentation with orientation
                    # and script detection - the default is page auto
                    # segmentation without the second two which can fail
                    # for some files.
                    config="--psm 1",
                )
                text_chunks.append(ocr_text)

        text = " ".join(text_chunks)
        # Need to be sure the OCR is actually working.
        print(submission_file, text)

    if file_format == "pdf-handwritten":
        # We will need to figure out a transcription process for
        # the small number of handwritten submissions - this might
        # be fastest to do manually.
        text = ""

    if file_format == "skip":
        text = ""

    if file_format == "txt":
        with open(submission_file, "r") as submission:
            text = submission.read()

    if file_format not in (
        "skip",
        "pdf",
        "pdf-mixed",
        "pdf-handwritten",
        "pdf-ocr",
        "pdf-vector-ocr",
        "txt",
    ):
        raise TypeError("Not a supported file_format")

    return text, skipped


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


all_args = set(sys.argv[1:])
apply_labels_only = False

if "apply_labels_only" in all_args:
    apply_labels_only = True
else:
    specific_inquiries = all_args
    print(f"Running for specific inquiries: {specific_inquiries}")

db = sqlite3.connect("inquiries.db", isolation_level=None)


if not apply_labels_only:
    db.executescript(
        """
        drop table if exists inquiry;
        create table inquiry (
            inquiry_shortname text primary key,
            name,
            context
        );

        drop table if exists submission;
        create table submission (
            inquiry_shortname references inquiry,
            submission_id,
            url,
            filepath,
            submitter,
            submitter_normalised,
            submitter_canonical,
            text,
            -- The following are the constructed categories for
            -- the submitter, and are derived by manual labelling.
            -- This is also available in the submission_label table for
            -- convenience.
            environmental integer,
            regional integer,
            consumptive integer,
            research integer,
            firstnations integer,
            resourcemanagers integer,
            government integer,
            commercialnon integer,
            notcategorisable integer,
            electedrep integer,
            primary key (inquiry_shortname, submission_id)
        );

        pragma journal_mode=WAL;
        pragma foreign_keys=1;

        """
    )

    session = requests.Session()

    db.execute("begin")

    with open("inquiries.csv", "r") as inquiries_file, open(
        "boilerplate.log", "w"
    ) as boilerplate_log:
        inquiries = csv.DictReader(inquiries_file, quoting=csv.QUOTE_ALL)

        for inquiry in inquiries:
            shortname = inquiry["inquiry_shortname"]

            # Used for testing - normal runs won't touch this.
            if specific_inquiries and shortname not in specific_inquiries:
                continue

            submissions_path = inquiry["submission_reference_file"]

            boilerplate_form = inquiry["boilerplate_regex"]
            if boilerplate_form:
                print(f"Detecting boilerplate with '{boilerplate_form}'")
                boilerplate_detector = re.compile(boilerplate_form)
            else:
                boilerplate_detector = None

            # make sure the submission specific file exists.
            try:
                os.mkdir(os.path.join("submissions", shortname))
            except FileExistsError:
                pass

            print(f"Processing {shortname=}")
            db.execute("insert into inquiry values(:inquiry_shortname, :name, :context)", inquiry)

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
                        r = session.get(
                            submission["submission_url"], allow_redirects=True
                        )

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
                        print(submission)
                        text, skipped = extract_text_from_file(
                            download_to,
                            submission_format,
                            boilerplate_detector,
                            int(submission["page_start"])
                            if submission["page_start"]
                            else 0,
                            int(submission["page_end"])
                            if submission["page_end"]
                            else 2**32,
                        )
                        boilerplate_log.writelines(skipped)

                    else:
                        text = ""

                    submission["inquiry_shortname"] = shortname
                    submission["text"] = text
                    submission["filepath"] = download_to
                    submission["submitter_normalised"] = normalise_submitter(
                        submission["submitter"]
                    )

                    db.execute(
                        """
                        insert into submission(
                            inquiry_shortname,
                            submission_id,
                            url,
                            filepath,
                            submitter,
                            submitter_normalised,
                            text
                        ) values (
                            :inquiry_shortname,
                            :id,
                            :submission_url,
                            :filepath,
                            :submitter,
                            :submitter_normalised,
                            :text
                        )
                        """,
                        submission,
                    )
    db.execute("commit")


# Merge in all of the current labels
db.execute("begin")

with open("submitter_labels.csv", "r") as f:
    db.execute("drop table if exists submission_label")
    db.execute(
        """
        create table submission_label (
            inquiry_shortname references inquiry,
            submission_id,
            label text,
            priority integer check (priority between 1 and 3),
            primary key (inquiry_shortname, submission_id, priority),
            foreign key (inquiry_shortname, submission_id) references submission
        )
        """
    )
    reader = csv.DictReader(f)
    for row in reader:
        # Update the new table with long format labels
        set_label = False
        key = (row["inquiry_shortname"], row["submission_id"])
        row["notcategorisable"] = ""

        for label in [
            "environmental",
            "regional",
            "consumptive",
            "research",
            "firstnations",
            "resourcemanagers",
            "government",
            "commercialnon",
            "electedrep",
        ]:
            if row[label]:
                set_label = True
                # Coerce everything to ints
                row[label] = int(row[label])
                try:
                    db.execute(
                        """
                        insert into submission_label values(?, ?, ?, ?)
                        """,
                        [*key, label, row[label]],
                    )
                except Exception:
                    print(f"{row} has duplicate priorities")
            else:
                # Empty strings become null in the wide table.
                row[label] = None

        if not set_label:
            row["notcategorisable"] = 1
            db.execute(
                """
                insert into submission_label values(?, ?, ?, ?)
                """,
                [*key, "notcategorisable", 1],
            )

        # Update the original table with wide format labels
        db.execute(
            """
            update submission set
                environmental = :environmental,
                regional = :regional,
                consumptive = :consumptive,
                research = :research,
                firstnations = :firstnations,
                resourcemanagers = :resourcemanagers,
                government = :government,
                commercialnon = :commercialnon,
                electedrep = :electedrep,
                notcategorisable = :notcategorisable
            where (inquiry_shortname, submission_id) =
                (:inquiry_shortname, :submission_id)
            """,
            row,
        )


print("Ingesting submitter/submission labels.")

# Write out all of submitter labels, to handle labelling of newly added
# submissions.
with open("submitter_labels_new.csv", "w") as f:
    writer = csv.writer(f, quoting=csv.QUOTE_ALL, dialect="excel")
    writer.writerow(
        [
            "inquiry_shortname",
            "submission_id",
            "filepath",
            "url",
            "submitter",
            "submitter_normalised",
            "submitter_canonical",
            "environmental",
            "regional",
            "consumptive",
            "research",
            "firstnations",
            "resourcemanagers",
            "government",
            "commercialnon",
            "electedrep",
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
            submitter_normalised,
            submitter_canonical,
            environmental,
            regional,
            consumptive,
            research,
            firstnations,
            resourcemanagers,
            government,
            commercialnon,
            electedrep
        from submission
        order by submitter_normalised
        """
    )

    for row in rows:
        writer.writerow(row)

db.execute("commit")
db.close()
