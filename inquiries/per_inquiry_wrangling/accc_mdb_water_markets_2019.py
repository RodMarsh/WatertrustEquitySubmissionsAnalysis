"""
The inquiry listing is div soup for these - we just walk through and find all
the links inside the frozen table extracted from each part of this
submission.

"""
from lxml import html

from csv_header import make_standard_csv

files = {
    "accc_mdb_water_markets_2019_issues.csv": "accc_mdb_water_markets_2019_issues.html",
    "accc_mdb_water_markets_2019_interim.csv": "accc_mdb_water_markets_2019_interim.html",
}


for output_file, input_file in files.items():
    with open(input_file, "r") as submission_table:
        html_string = submission_table.read()

    print(output_file)

    with open(output_file, "w") as submissions_file:
        writer = make_standard_csv(submissions_file)
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
