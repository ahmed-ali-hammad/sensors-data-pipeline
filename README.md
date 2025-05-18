<h3 align="center">Sensors Data Pipeline</h3>

<div align="center">
  <img src="https://img.shields.io/badge/status-active-success.svg" />
  <img src="https://img.shields.io/badge/python-3.13-blue" />
</div>

---

<p align="center">
    <br> 
</p>

## 📝 Table of Contents
- [About](#about)
- [Getting Started](#getting-started)
- [Built Using](#built-using)

## 🧐 About <a name = "about"></a>
This project provides a CLI-based pipeline to ingest and retrieve sensor data from an object store (Minio). It uses PostgreSQL for structured mapping data (`sensor_name`, `sensor_uuid`) and TimescaleDB for time-series sensor measurements (`timestamp`, `sensor_value`, `sensor_uuid`).

## 🏁 Getting Started <a name = "getting_started"></a>
These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. 

### Env Varialbes
Before starting the project setup, make sure to fill these values in the `config/.env` file:

```bash
MINIO_ENDPOINT     # Note: Make sure not to include the protocol (http/https). Just use host:port.
MINIO_ACCESS_KEY   # Note: Your access key for the object store (Minio).
MINIO_SECRET_KEY   # Note: Your secret key for the object store (Minio).
```

### Prerequisites
 - [Docker](https://docs.docker.com/)
 - [Docker Compose](https://docs.docker.com/compose/)

### Installing
If you're opening this project using [devcontainers](https://containers.dev/) then your docker container should be ready to go!

Otherwise you will need to start the docker compose environment `docker compose up` and open a shell into the container `sensors-data-pipeline-dev`.

```bash
$ docker compose up
$ docker exec -it sensors-data-pipeline-dev /bin/bash   # spawns a shell within the docker container
$ pipenv shell  # spawns a shell within the virtualenv 
$ pip install -e .
```

### Database Migrations
*Note: The following three Alembic commands are useful to document here, but if you're setting up this project, you only need to apply the migrations (last command only)*

```bash
# init the migrations folder
$ alembic init migrations  

# create a new migration version
$ alembic -c migrations_db/alembic.ini revision --autogenerate -m "message"
$ alembic -c migrations_timescale_db/alembic.ini revision --autogenerate -m "message"

# apply migrations
$ alembic -c migrations_db/alembic.ini upgrade head
$ alembic -c migrations_timescale_db/alembic.ini upgrade head
```

### ▶️ Running the Worker
This project uses CLI entry points defined in pyproject.toml to run the scripts:

```bash
# Run the ingestion pipeline, no arguments required
ingest-sensors-data-from-storage
```

```bash
# Retrieve sensor readings
retrieve-sensor-readings --arguments
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

### 🧪 Running the tests <a name = "tests"></a>
- [pytest](https://docs.pytest.org/) is used to run unit and integration tests.

```bash
# To run unit and integration tests
$ pytest .
``` 

### Code Style & Linting
The following tools are run during pipelines to enforce code style and quality.

 - [flake8](https://flake8.pycqa.org/en/latest/) for linting
 - [isort](https://pycqa.github.io/isort/) for import sorting
 - [black](https://black.readthedocs.io/en/stable/) for code style

### Python Package Management
- [pipenv](https://pipenv.pypa.io/en/latest/) is used to manage Python packages. 

```bash
$ pipenv shell  # spawns a shell within the virtualenv
$ pipenv install  # installs all packages from Pipfile
$ pipenv install --dev # installs all packages from Pipfile, including dev dependencies
$ pipenv install <package1> <package2>  # installs provided packages and adds them to Pipfile
$ pipenv update  # update package versions in Pipfile.lock, this should be run frequently to keep packages up to date
$ pipenv uninstall package # uninstall a package 
$ pipenv uninstall package  --categories dev-packages # uninstall a dev package
```

## ⛏️ Built Using <a name = "built_using"></a>
 - [PostgreSQL](https://www.postgresql.org/) - Database.
 - [TimescaleDB](https://www.timescale.com/) - Time Series Database
 - [SQLAlchemy](https://www.sqlalchemy.org/) - ORM.
 - [Alembic](https://alembic.sqlalchemy.org/en/latest/) - Database Migration Tool.