import csv


def make_standard_csv(submissions_file):
    return csv.DictWriter(
        submissions_file,
        [
            "id",
            "submitter",
            "submission_url",
            "format",
            "attachment_urls",
            "page_start",
            "page_end",
        ],
        quoting=csv.QUOTE_ALL,
    )
