"""
The inquiry listing is div soup for these - we just walk through and find all
the links inside the frozen table extracted from each part of this
submission.

"""
import csv

from lxml import html

files = {
    "accc_mdb_water_markets_2019_issues_check.csv": "accc_mdb_water_markets_2019_issues.html",
    "accc_mdb_water_markets_2019_interim_check.csv": "accc_mdb_water_markets_2019_interim.html",
}


for output_file, input_file in files.items():
    with open(input_file, "r") as submission_table:
        html_string = submission_table.read()

    print(output_file)

    with open(output_file, "w") as submissions_file:
        writer = csv.DictWriter(
            submissions_file,
            ["id", "submitter", "submission_url", "format", "attachment_urls"],
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()

        submission_listing = html.fragment_fromstring(html_string)
        submission_listing.make_links_absolute("https://www.accc.gov.au/")

        # Choose by their file
        links = submission_listing.xpath('//span[@class="file"]/a')

        for i, link in enumerate(links):
            submission = {}

            submission["id"] = i
            submission["format"] = "pdf"
            submission["attachment_urls"] = ""
            submission["submitter"] = "".join(link.itertext()).strip()
            submission["submission_url"] = link.attrib["href"]

            writer.writerow(submission)
