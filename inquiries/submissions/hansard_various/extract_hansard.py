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
            -- second reading speeches on particular bills
            replace(title, '\n', ' ') in (
                'BILLS Water Amendment (Restoring Our Rivers) Bill 2023 Second Reading',
                'WATER BILL 2007 WATER (CONSEQUENTIAL AMENDMENTS) BILL 2007 Second Reading',
                'BILLS Water Amendment Bill 2015 Second Reading',
                'BILLS Water Amendment (Water for the Environment Special Account) Bill 2012 Second Reading',
                'WATER AMENDMENT BILL 2008 Second Reading',
                'BILLS Water Amendment Bill 2018 Second Reading',
                'BILLS Water Amendment (Long-term Average Sustainable Diversion Limit Adjustment) Bill 2012 Second Reading',
                'BILLS Water Amendment (Review Implementation and Other Measures) Bill 2015 Second Reading',
                'BILLS National Water Commission (Abolition) Bill 2015 Second Reading',
                'BILLS Water Legislation Amendment (Inspector-General of Water Compliance and Other Measures) Bill 2021 Second Reading',
                'BILLS Register of Foreign Ownership of Agricultural Land Amendment (Water) Bill 2016 Second Reading',
                'BILLS Water Amendment (Indigenous Authority Member) Bill 2019 Second Reading',
                'BILLS Environment Protection and Biodiversity Conservation Amendment (Expanding the Water Trigger) Bill 2023 Second Reading',
                'Federation Chamber BILLS National Water Commission Amendment Bill 2012 Second Reading',
                'BILLS Water Legislation Amendment (Sustainable Diversion Limit Adjustment) Bill 2016 Second Reading'
                )
            )
            -- Only choose pages with nominated speakers/excluding some of the procedural elements such as divisions.
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
