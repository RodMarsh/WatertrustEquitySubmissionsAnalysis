"""
This extracts the relevant Hansard speeches from the data download using the 
approach documented here: https://github.com/SamHames/hansard-tidy

This uses the web version of parlinfo for consistency across time, but
unfortunately the source URLs are not stable in this format. For this reason
the data snapshot is stored directly in the repo to aid reproducibility post
data extract.

The data that is extracted is based on the titles of debates. The specific
string matches are:


    lower(title) like '%water%bill 2007%': to match the Water Bill 2007 or the
        related Water (Consequential Amendments) Bill 2007
    lower(title) like '%basin authority%': murray-darling basin Authority (MDBA)
    lower(title) like '%basin plan%': murray-darling basin plan
    lower(title) like '%restoring our rivers%': Water (Restoring our Rivers) Bill 2023

Only speeches that occur as part of debates which match the above strings, and
have a nominated 'speaker' in the Hansard metadata are included - this may
exclude some questions, and occasionally the speaker metadata is not
perfectly accurate.

The data was up-to-date as of 2023-12-18: some proofs and URLs may changed
since that point.

"""

import csv
import sqlite3

from lxml import html

db = sqlite3.connect("tidy_hansard.db")

with open("../../hansard_speeches.csv", "w", newline="") as f:
    writer = csv.writer(f, quoting=csv.QUOTE_ALL)

    writer.writerow(
        [
            "id",
            "submitter",
            "submission_url",
            "format",
            "attachment_urls",
            "page_start",
            "page_end",
        ]
    )

    rows = db.execute(
        """
        select
                page_id as id,
                (select value from metadata where key = 'Speaker' and page_id=pp.page_id) as submitter,
                url as submission_url,
                'txt' as format,
                '' as attachment_urls,
                '' as page_start,
                '' as page_end,
                page_html
        from proceedings_page pp
        inner join debate using(debate_id)
        where
                pp.date >= '2003-01-01'
            and (
                -- Select debates by that match four specific
                -- content areas, spanning 2007-current
                -- and the MDBA and Basin plan in between
                lower(title) like '%water%bill 2007%' or
                lower(title) like '%basin authority%' or
                lower(title) like '%basin plan%' or
                lower(title) like '%restoring our rivers%'
            )
            and page_id in (
                select page_id
                from metadata
                where key = 'Speaker'
            )
        """
    )

    for row in rows:
        # Write the CSV header row
        writer.writerow(row[:-1])

        speech_text = html.fragment_fromstring(row[-1])
        filename = f"{row[0]}.txt"

        with open(filename, "w") as f:
            f.write(" ".join(speech_text.itertext()))
