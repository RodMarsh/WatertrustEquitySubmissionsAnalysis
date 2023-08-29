"""
The inquiry listing is a horrible dynamically generated table with no URL
changing pagination. This script prepares turn the HTML table as saved from
firefox devtools into the format needed for the downloader.

"""
import csv

from lxml import html

files = ["pc_nwf_2020_initial.html", "pc_nwf_2020_postdraft.html"]


with open("pc_nwf_2020_check.csv", "w") as submissions_file:
    writer = csv.DictWriter(
        submissions_file,
        ["id", "submitter", "submission_url", "format", "attachment_urls"],
        quoting=csv.QUOTE_ALL,
    )
    writer.writeheader()

    for file in files:
        with open(file, "r") as submission_table:
            html_string = submission_table.read()

        table = html.fragment_fromstring(html_string)

        # Skip the header row
        rows = table.xpath("//tbody/tr")[1:]

        submission = {}

        for i, row in enumerate(rows):
            # For this commission there are multiple rows per submission. PDFs
            # of all submissions are provided, but some of them have been
            # converted from word - the originals are provided separately,
            # along with any attachments...
            id_cell, submission_cell, _, _ = row.xpath("td")
            submission_details = submission_cell.findall("a")[0]
            link_text = "".join(submission_details.itertext())

            try:
                # If we can extract the submission_id, this is the main
                # row for this submission.
                if id_cell.text and id_cell.text.startswith("DR"):
                    submission_id = id_cell.text
                else:
                    submission_id = str(int(id_cell.text))

                # Write the previous submission
                if submission:
                    submission["attachment_urls"] = "|".join(attachment_urls)

                    writer.writerow(submission)

                submission = {}
                submission["id"] = submission_id
                submission["format"] = "pdf"
                assert len(link_text.split(" (PDF")) == 2
                submission["submitter"] = link_text.split(" (PDF")[0]
                submission["submission_url"] = submission_details.attrib["href"]

                attachment_urls = []

            except (TypeError, ValueError) as e:
                if link_text.startswith("Attachment"):
                    attachment_urls.append(submission_details.attrib["href"])
                else:
                    continue

        writer.writerow(submission)
