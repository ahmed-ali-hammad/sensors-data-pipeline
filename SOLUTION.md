## 📝 General Notes

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. 

Before starting the project setup, make sure to fill these values in the `config/.env` file:

```bash
MINIO_ENDPOINT     # Note: Make sure not to include the protocol (http/https). Just use host:port.
MINIO_ACCESS_KEY   # Note: Your access key for the object store (Minio).
MINIO_SECRET_KEY   # Note: Your secret key for the object store (Minio).
```

#### 📋 Prerequisites
 - [Docker](https://docs.docker.com/)
 - [Docker Compose](https://docs.docker.com/compose/)

#### 🔧 Installing

If you're opening this project using [devcontainers](https://containers.dev/) then your docker container should be ready to go!

Otherwise you will need to start the docker compose environment `docker compose up` and open a shell into the container `sensors-data-pipeline-dev`.

```bash
# These four commands are necessary only if you're not using devcontainers. If you're using devcontainers, you can skip them and proceed directly to the Database Migrations section.
$ docker compose up
$ docker exec -it sensors-data-pipeline-dev /bin/bash   # spawns a shell within the docker container
$ pipenv shell  # spawns a shell within the virtualenv 
$ pip install -e .
```

#### 🔄 Database Migrations
This project uses two separate databases. To set up the required tables in both databases, run the following migration commands:
```bash
# Apply migrations for the main database
$ alembic -c migrations_db/alembic.ini upgrade head

# Apply migrations for the TimescaleDB (used for timeseries data)
$ alembic -c migrations_timescale_db/alembic.ini upgrade head
```

#### ▶️ Running the Scripts
This project uses CLI entry points defined in pyproject.toml to run the scripts:
```bash
# Run the ingestion pipeline
ingest-sensors-data-from-storage

# Retrieve sensor readings. This entrypoint requires specific arguments, see the notes in Task 2 for detailed usage and examples
retrieve-sensor-readings
```

## 📝 Notes for Task 1
* 🗃️ Database Choice:

PostgreSQL is chose for storing the mapping data (`sensor_name`, `sensor_uuid`) because it is a powerful relational database that is well-suited for structured data. The mapping file contains `sensor_name`, `sensor_uuid`, which naturally fit into a tabular schema with clearly defined relationships and constraints. 

PostgreSQL also supports indexing, which can significantly speed up lookups — for example, by indexing the `sensor_name` column, read queries will remain efficient when the size of the mapping data grows.

* 🛠️ Database Schema:

The mapping data (`sensor_name`, `sensor_uuid`) fits naturally into a single relational table, which serves as a metadata table to support lookups and relationships with other tables.

At this moment, no indexes have been added to the `sensor_info` table. However, if the dataset grows, we can add an index on the `sensor_name` column to improve query performance.

* 🚀 Entrypoint

This project uses `pyproject.toml` to define the entry points for running the scripts.

Tasks 01 and 02 share a common entry point: `ingest-sensors-data-from-storage`.

To run the script, first follow the setup instructions defined in the **General Notes** section to configure the project and initialize the databases. Once everything is set up, simply run the following command from the root directory:

```bash
$ ingest-sensors-data-from-storage
```

The ingestion process can take approximately 45 minutes to fetch and store the complete dataset.

## 📝 Notes for Task 2
* 🗃️ Database Choice:

I went with TimescaleDB because it is specifically optimized for handling time-series data (`timestamp`, `sensor_uuid`, `sensor_value`). TimescaleDB is built on top of PostgreSQL and is optimum in our case because of:

- Efficient storage and compression for time-series data.
- Faster querying and aggregation over time intervals.
- Full SQL support, making it easier to integrate and query data.

* 🛠️ Database Schema:

`sensor_measurement` is the core table and it's structured to store the following fields:

- id: primary key
- sensor_uuid
- timestamp
- sensor_value

An index has been added to the `timestamp` field to speed up filtering. Also, A unique constraint on (`sensor_uuid`, `timestamp`) ensures no duplicate readings from the same sensor at the same time.

This schema is ideal for time-series workloads because:

- Time-based indexing (timestamp) allows efficient filtering and aggregation over time ranges.
- Sensor-level uniqueness ensures data integrity across noisy input streams.
- UUID-based sensor identification separates metadata (like `sensor_name`) from measurement data, which keeps the schema normalized and clean.


* 🚀 Entrypoint

This project uses pyproject.toml to define the entry points for running the scripts.

Tasks 01 and 02 share a common entry point: `ingest-sensors-data-from-storage`.

To run the script, first follow the setup instructions defined in the **General Notes** section to configure the project and initialize the databases. Once everything is set up, simply run the following command from the root directory:

```bash
$ ingest-sensors-data-from-storage
```
The ingestion process can take approximately 45 minutes to fetch and store the complete dataset.

## 📝 Notes for Task 3
* ⚙️ Scalability and Performance Considerations:

To ensure the code handles growing data volumes gracefully, the `get_sensor_readings` method is implemented as an asynchronous generator that retrieves and yields sensor data in batches. This allows the system to stream large datasets efficiently without overwhelming memory.

Key design choices for scalability:

- Batch Processing: The method uses a default batch size of 500 records and can be adjusted depending on performance needs.
- Pagination Support: The `page_number` and `page_size` parameters offer clients precise control over how much data to retrieve.


* 🚀 Entrypoint

To run the script, first follow the setup instructions defined in the **General Notes** section to configure the project and initialize the databases. 

Once everything is set up, you can use the following entrypoint to retrieve sensor measurements:

```bash
retrieve-sensor-readings
```

- Required Arguments:
    - sensor-name       :TEXT
    - start-timestamp   :TEXT
    - end-timestamp     :TEXT

- Optional Arguments:
    - page-number       :INTEGER
    - page-size         :INTEGER

For example, to fetch readings for `sensor_00007` between `"2012-12-31T23:07:00+00"` and `"2013-02-16T11:03:00+00"` with pagination:

```bash
retrieve-sensor-readings \
--sensor-name sensor_00007 \
--start-timestamp "2012-12-31T23:07:00+00" \
--end-timestamp "2013-02-16T11:03:00+00" \
--page-number 2 \
--page-size 10
```

If `--page-number` and `--page-size` are omitted, the script will fetch all available records within the specified time range.

*Note*: Make sure to first run the ingestion script from task_01/task_02 to populate the database. The initial ingestion process can take approximately 45 minutes to fetch and store the complete dataset.

## 📝 Notes for Task 4
* ...