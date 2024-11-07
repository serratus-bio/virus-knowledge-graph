import xml.sax

import dask.dataframe as dd
import pandas as pd


class BioSamplesMatcherHandler(xml.sax.ContentHandler):
    """
    SAX handler class to read in information from a BioSamples XML file
        - Reads the title, paragraph, and attributes of each BioSample
        - Information is stored in a Dask DataFrame with multiple partitions
    """

    def __init__(self, partition_size, data_folder) -> None:
        super().__init__()
        self.records = []
        self.attribute_dict = {}
        self.biosample_id = ""
        self.content_dict = {}
        self.is_title = False
        self.is_paragraph = False
        self.attribute_name = ""
        self.partition_size = partition_size
        self.data_folder = data_folder
        self.partition_count = 0

    def startElement(self, name, attrs):
        if name == "BioSample":
            self.biosample_id = attrs["accession"]
        elif name == "Title":
            self.is_title = True
        elif name == "Paragraph":
            self.is_paragraph = True
        elif name == "Attribute":
            try:
                self.attribute_name = attrs["harmonized_name"]
            except KeyError:
                self.attribute_name = attrs["attribute_name"]

    def characters(self, content):
        if self.is_title:
            self.content_dict["title"] = content.lower()
            self.is_title = False
        elif self.is_paragraph:
            self.content_dict["paragraph"] = content.lower()
            self.is_paragraph = False
        elif self.attribute_name != "":
            self.attribute_dict[self.attribute_name] = content.lower()
            self.attribute_name = ""

    def endElement(self, name):
        if name == "BioSample":
            self.content_dict["attributes"] = self.attribute_dict
            self.content_dict["biosample_id"] = self.biosample_id
            self.records.append(self.content_dict)
            self.attribute_dict = {}
            self.content_dict = {}

            # Process records in batches
            if (
                len(self.records) >= self.partition_size
            ):  # Set the batch size for partitions
                self.save_to_disk()

    def endDocument(self):
        if self.records:
            # Save remaining records
            self.save_to_disk()
        print("Finished parsing BioSamples XML file")

    def save_to_disk(self):
        # Convert current batch of records to a DataFrame and append to Dask DataFrame
        batch_df = pd.DataFrame(self.records, columns=["biosample_id", "title", "paragraph", "attributes"])
        batch_df.to_csv(
            f"{self.data_folder}/biosamples_{self.partition_count}.csv", index=False
        )
        self.partition_count += 1
        # Clear records for the ext batch
        self.records = []
