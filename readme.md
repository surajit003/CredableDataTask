# 📊 Credable Data Task – Django + ETL + PostgreSQL

This project is a hybrid data ingestion pipeline and Django web backend powered by:

- 🧬 **ETL scripts** using [Polars](https://www.pola.rs/) for fast data processing
- 🌐 **Django** for web/API framework
- 🐘 **PostgreSQL** as the main database
- 🐳 **Docker Compose** for local dev and orchestration

---

## 🚀 Features

- Upload and parse CSV/JSON data
- Flatten nested structures (JSON)
- Clean + normalize using Polars (string trimming, type casting, datetime parsing)
- Load into PostgreSQL
- Unit tested and containerized

---

## 📦 Tech Stack

| Layer        | Tech             |
|--------------|------------------|
| Backend      | Django, Python 3.11 |
| ETL          | Polars, Structlog |
| Database     | PostgreSQL 14     |
| Container    | Docker + Docker Compose |
| Testing      | `unittest` + mocks |
| Config       | `python-decouple` for env management |

---

## 🧰 Project Structure
---

## ⚙️ Environment Variables

Create a `.env` file in the root with the following:

```env
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
```

## 🐳 Docker Setup
Build and Start Containers
```
docker-compose up --build
```
Django runs at: http://localhost:8000

PostgresSQL exposed on localhost:5432

## 🔄 Run ETL Pipeline
There is a sample CSV file in scripts/downloads which has been used for building the ETL pipeline.
The file is named `customers-100.csv` and can be used to test the ETL pipeline.

Run the full ingestion pipeline:
```
docker exec -it django_etl_app python etl/ingest.py --filename customers-100.csv
```

## 🧪 Testing
Run the django tests:
```
docker exec -it django_etl_app python manage.py test
```

Run the ETL tests:
```
docker exec -it django_etl_app  python -m etl.tests.test_transform
```

## 📘 API: Get Customers
GET /api/customers/
Fetch a paginated, filterable, and searchable list of customers.

## 🔐 Auth
Using the simple `Token` authentication provided by Django REST Framework.

### 📥 Example Request
```
curl -X GET "http://localhost:8000/api/customers/?search=alice&country=USA&ordering=-subscription_date" \
  -H "Authorization: Token abc123"
```

### 📤 Example Response
```json
{
  "next": "http://localhost:8000/api/customers/?cursor=abc...",
  "previous": null,
  "results": [
    {
      "index": 1,
      "customer_id": "ABC123",
      "first_name": "Alice",
      "last_name": "Smith",
      "company": "Acme Corp",
      "city": "New York",
      "country": "USA",
      "phone_1": "123-456-7890",
      "phone_2": null,
      "email": "alice@example.com",
      "subscription_date": "2023-12-01",
      "website": "https://acme.com",
      "source_file": "customers.csv",
      "ingested_at": "2024-01-01T10:30:00Z"
    }
  ]
}
```

### Notes:
By default, there is a single user created with the following credentials:
- Username: `admin`
- Password: `admin123`

### Running outside Docker

### Django
To run the Django server outside of Docker, you will need to install the dependencies:
```
pip install -r requirements.txt
```

Then you can run the Django server:
```
python manage.py migrate
python manage.py runserver
```


### ETL
To run the ETL pipeline outside of Docker, you will need to install the dependencies:
```
pip install -r requirements.txt
```

Then you can run the ETL script:
```
python etl/ingest.py --filename customers-100.csv
```

---
High level overview of the Project for scale

### Data Ingestion Layer
🔹 Purpose
Automate the retrieval of files from external sources (e.g., SFTP servers), support multiple file formats (CSV, JSON),
and implement robust failure handling.

- Supported Formats
Primary: CSV, JSON

- Schema Validation
Early schema enforcement and validation to catch malformed files before processing.

- Error Handling & Monitoring
Retry mechanisms with exponential backoff.

Integration with Slack, email, and Sentry for failure alerts.

Audit logs capturing filename, status, timestamps, and error traces.

### Data Processing Layer
🔹 Purpose
- Transform raw ingested data into clean, structured, and business-ready datasets.

🔹 Tools & Frameworks
🚀 Apache Spark
- Distributed processing engine for large-scale data.

Handles heavy transformations, joins, aggregations, and batch jobs efficiently.

⚡ Polars (Python)
In-memory, lightning-fast columnar processing.

Ideal for sampling, validation, and small- to mid-sized data curation.

🔹 Transformations
- Flatten nested structures.

- Standardize field names and formats (dates, currencies, etc.).

- Perform deduplication, null handling, and outlier detection.

🔹 Data Quality Rules
- Rule-based validations (field constraints, regex patterns, value ranges).

- Quarantine invalid records with reason logs.

- Configurable thresholds for record rejection vs. warning.

3. Data Storage Layer
🔹 Purpose
Store curated datasets in a scalable, queryable, and cost-effective architecture.

🔹 Architecture
🗂️ Amazon S3
Central data lake for storing:

raw/ – Original ingested files

processed/ – Cleaned intermediate outputs

curated/ – Business-ready, enriched datasets

🧊 Apache Iceberg
ACID-compliant table format over S3.

Key features:

- Time travel and snapshot isolation

- Schema evolution without rewriting full datasets

- Partition pruning and hidden metadata columns for query efficiency

🗃️ Catalog Integration
Table metadata managed via AWS Glue Data Catalog or Hive Metastore.

- Enables schema discovery by Spark and Athena.

- Automated updates after each job run.

4. Data Query Layer
🔹 Purpose
Expose curated datasets for analytics, business reporting, and external access.

🔹 Tools
🔍 Amazon Athena
Serverless SQL queries on Iceberg tables over S3.
