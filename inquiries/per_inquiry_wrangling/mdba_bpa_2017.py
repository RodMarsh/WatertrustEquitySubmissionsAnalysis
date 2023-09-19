"""
Nicely formatted UL with LI and A's inside.

"""
import re

from lxml import html

from csv_header import make_standard_csv


extract_submitter = re.compile(
    r"(No\. ?[0-9]+,)|(\([0-9]+(.?[0-9]+)? .B\) \((pdf|html|PDF)\))"
)

files = ["mdba_bpa_2017_individual.html", "mdba_bpa_2017_organisation.html"]

with open("mdba_bpa_2017.csv", "w") as submissions_file:
    writer = make_standard_csv(submissions_file)
    writer.writeheader()

    identifier = 1

    for input_file in files:
        with open(input_file, "r") as submission_table:
            html_string = submission_table.read()

        print(input_file)

        submission_listing = html.fragment_fromstring(html_string)
        links = submission_listing.xpath("//a")

        for link in links:
            link_info = "".join(link.itertext())

            submission = {}
            # Note that the ID's are not unique on their page, so we'll generate our own :(
            submission["id"] = str(identifier)
            submission["submitter"] = extract_submitter.sub("", link_info).strip()
            submission["submission_url"] = link.attrib["href"] + "/download"
            # Note there is one file with a weird structure - it's labelled as
            # html as it actually links to a document that links to the
            # submission and an MDBA response. This override is specific to
            # that file only.
            if submission["id"] == "229":
                submission[
                    "submission_url"
                ] = "https://s3-ap-southeast-2.amazonaws.com/ehq-production-australia/7d69d2849c0ad2e2856e5f9153a07e307e2ccfe0/documents/attachments/000/051/779/original/Mal_Peters.pdf"
            submission["format"] = "pdf"
            submission["attachment_urls"] = ""

            writer.writerow(submission)

            identifier += 1
