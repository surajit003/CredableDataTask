1. Data Ingestion
○ Retrieve data files from an SFTP location.
○ Handle various data formats (e.g. CSV & JSON).
○ Implement error handling for failed data transfers with alerts.


2. Data Processing
○ Flatten and clean the ingested data, as necessary. We want to see curated
datasets for usage and consumption by business users at the end of the pipeline
process.
○ Apply any necessary data quality measures to get the data into a state ready for
business consumption.

3. API Development
○ Create an API that allows external clients to access the processed data.
○ Implement filtering by date and cursor-based pagination to handle large datasets.
○ Design the API to ensure basic security and rate limiting.
