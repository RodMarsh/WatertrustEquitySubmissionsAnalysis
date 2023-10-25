"""
The inquiry listing is a horrible dynamically generated table with no URL
changing pagination. This script prepares turn the HTML table as saved from
firefox devtools into the format needed for the downloader.

"""
from lxml import html

from csv_header import make_standard_csv

files = {
    "pc_nwf_2020_initial.csv": "pc_nwf_2020_initial.html",
    "pc_nwf_2020_postdraft.csv": "pc_nwf_2020_postdraft.html",
    "pc_mdbp_implementation_2023.csv": "pc_mdbp_implementation_2023.html",
    "pc_mdbp_fiveyear_2018_initial.csv": "pc_mdbp_fiveyear_2018_initial.html",
    "pc_mdbp_fiveyear_2018_postdraft.csv": "pc_mdbp_fiveyear_2018_postdraft.html",
}


for output_file, input_file in files.items():
    with open(input_file, "r") as submission_table:
        html_string = submission_table.read()

    print(output_file)

    with open(output_file, "w") as submissions_file:
        writer = make_standard_csv(
            submissions_file,
        )
        writer.writeheader()

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
            submission_links = submission_cell.findall("a")
            if submission_links:
                submission_details = submission_links[0]
            else:
                # No link to the submission - just continue
                continue
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
