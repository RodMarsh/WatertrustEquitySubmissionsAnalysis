"""
The inquiry listing is a horrible dynamically generated table with no URL
changing pagination. This script prepares turn the HTML table as saved from
firefox devtools into the format needed for the downloader.

"""
from lxml import html

from csv_header import make_standard_csv

with open("select_committee_fph_2021.html", "r") as submission_table:
    html_string = submission_table.read()

table = html.fragment_fromstring(html_string)

table.make_links_absolute("https://www.parliament.nsw.gov.au")

rows = table.xpath("//tbody/tr")

with open("select_committee_fph_2021.csv", "w") as submissions_file:
    writer = make_standard_csv(submissions_file)
    writer.writeheader()

    for i, row in enumerate(rows):
        urls = row.xpath("td/a")

        submission = {}

        if urls:
            main = urls[0]
            info = main.text

            submission["submission_url"] = main.attrib["href"]

            submission["attachment_urls"] = "|".join(
                url.attrib["href"] for url in urls[1:]
            )
            submission["format"] = "pdf"

        else:
            td = row.xpath("td")[0]
            info = td.text
            submission["submission_url"] = ""
            submission["attachment_urls"] = ""
            submission["format"] = ""

        sub_id, submitter = info.split("\u00A0")
        # every submission has "No. " before the actual ID
        # Attaches are new rows in the table... :(
        # If the ID doesn't convert to an integer just skip the row.
        submission_id = sub_id.strip()[4:]
        try:
            int(submission_id)
        except ValueError:
            continue

        submission["id"] = submission_id

        submission["submitter"] = submitter.strip()

        writer.writerow(submission)
