"""
The inquiry listing is a horrible dynamically generated table with no URL
changing pagination. This script prepares turn the HTML table as saved from
firefox devtools into the format needed for the downloader.

"""
from lxml import html

from csv_header import make_standard_csv

with open("select_committee_restoring_rivers_2023.html", "r") as submission_table:
    html_string = submission_table.read()

table = html.fragment_fromstring(html_string)

# Turn the relative links into the absolute links
table.make_links_absolute("https://www.aph.gov.au")

rows = table.xpath("//tbody/tr")

with open("select_committee_restoring_rivers_2023.csv", "w") as submissions_file:
    writer = make_standard_csv(submissions_file)
    writer.writeheader()

    for i, row in enumerate(rows):
        tds = row.xpath("td")
        assert len(tds) == 4

        submission = {}
        submission["id"] = tds[0].text

        try:
            # Named submissions
            submission["submitter"] = tds[1].xpath("strong")[0].text
        except IndexError:
            # Confidential and withheld submissions
            submission["submitter"] = tds[1].text

        urls = tds[1].xpath("a")

        if urls:
            submission["submission_url"] = urls[0].attrib["href"]
            submission["attachment_urls"] = "|".join(
                url.attrib["href"] for url in urls[1:]
            )
            submission["format"] = "pdf"
        else:
            submission["submission_url"] = ""
            submission["attachment_urls"] = ""
            submission["format"] = ""

        writer.writerow(submission)
