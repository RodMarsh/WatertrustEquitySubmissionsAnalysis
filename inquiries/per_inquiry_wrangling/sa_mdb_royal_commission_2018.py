"""
The inquiry listing is a horrible dynamically generated table with no URL
changing pagination. This script prepares turn the HTML table as saved from
firefox devtools into the format needed for the downloader.

"""
from lxml import html

from csv_header import make_standard_csv

with open("sa_mdb_royal_commission_2018.html", "r") as submission_table:
    html_string = submission_table.read()

table = html.fragment_fromstring(html_string)

# Skip the header row, that isn't marked up with <th> :(
rows = table.xpath("//tbody/tr")[1:]

with open("sa_mdb_royal_commission_2018.csv", "w") as submissions_file:
    writer = make_standard_csv(submissions_file)
    writer.writeheader()

    for i, row in enumerate(rows):
        urls = row.xpath("td//a")

        submission = {}

        submission["id"] = i
        submission["attachment_urls"] = ""

        if urls:
            # Confirm all URLs are to the same file when there are multiple authors.
            assert len(set(url.attrib["href"] for url in urls)) == 1
            submission["submission_url"] = urls[0].attrib["href"]
            submission["format"] = "pdf"
            submission["submitter"] = " | ".join(url.text for url in urls)

        else:
            submission["submission_url"] = ""
            submission["format"] = ""

            cells = row.xpath("td")
            # This will include everything up to a <br> tag, which
            # is used to separate the author from the organisation.
            submission["submitter"] = cells[0].text.strip()

        writer.writerow(submission)
