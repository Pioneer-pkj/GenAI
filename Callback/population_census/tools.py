from google.cloud import storage
from google.cloud import bigquery

project = "gcai-sep-26"

def list_buckets():
    """Lists all buckets."""
    storage_client = storage.Client(project=project)
    buckets = storage_client.list_buckets()
    bucket_names = [bucket.name for bucket in buckets]
    for name in bucket_names:
        print(name)
    return {"buckets": bucket_names}

def create_bucket(bucket_name: str, storage_class: str = "STANDARD", location: str = "us"):
    """
    Creates a new GCS bucket with the specified storage class and location.

    Args:
        bucket_name (str): The globally unique name of the bucket to create.
        storage_class (str): Storage class for the bucket. Valid options:
                             'STANDARD', 'NEARLINE', 'COLDLINE', 'ARCHIVE'.
                             Defaults to 'STANDARD'.
        location (str): Region or multi-region (e.g., 'us', 'asia', 'us-central1').
                        Defaults to 'us'.
    """
    storage_client = storage.Client(project=project)
    bucket = storage_client.bucket(bucket_name)
    bucket.storage_class = storage_class.upper()
    new_bucket = storage_client.create_bucket(bucket, location=location)
    print(
        "Created bucket {} in {} with storage class {}".format(
            new_bucket.name, new_bucket.location, new_bucket.storage_class
        )
    )
    return {"name": new_bucket.name, "location": new_bucket.location, "storage_class": new_bucket.storage_class}

def delete_bucket(bucket_name: str):
    """Deletes a bucket. The bucket must be empty."""
    storage_client = storage.Client(project=project)
    bucket = storage_client.get_bucket(bucket_name)
    bucket.delete()
    print(f"Bucket {bucket_name} deleted")
    return {"deleted": bucket_name}

def load_csv_to_bq(
    bucket_name: str,
    source_file_name: str,
    dataset_id: str,
    table_id: str,
    autodetect: bool = True,
    write_disposition: str = "WRITE_APPEND",
):
    """
    Loads a CSV file from a Google Cloud Storage bucket into a BigQuery table.

    Args:
        bucket_name (str): Name of the GCS bucket where the CSV file is located.
        source_file_name (str): Path or filename of the CSV in the bucket (e.g., 'data.csv' or 'folder/sales.csv').
        dataset_id (str): The BigQuery dataset ID where the table belongs.
        table_id (str): The destination BigQuery table ID.
        autodetect (bool): Automatically infer the table schema from the CSV file. Defaults to True.
        write_disposition (str): Specifies the action if destination table already exists.
                                 Options: 'WRITE_APPEND', 'WRITE_TRUNCATE', 'WRITE_EMPTY'. Defaults to 'WRITE_APPEND'.
    """
    client = bigquery.Client(project=project)
    table_ref = f"{project}.{dataset_id}.{table_id}"

    if source_file_name.startswith("gs://"):
        uri = source_file_name
    else:
        uri = f"gs://{bucket_name}/{source_file_name.lstrip('/')}"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=autodetect,
        write_disposition=getattr(
            bigquery.WriteDisposition, write_disposition.upper(), bigquery.WriteDisposition.WRITE_APPEND
        ),
    )

    load_job = client.load_table_from_uri(uri, table_ref, job_config=job_config)
    print(f"Starting job {load_job.job_id} to load {uri} into {table_ref}...")
    load_job.result()

    destination_table = client.get_table(table_ref)
    print(f"Loaded {destination_table.num_rows} rows into {table_ref}")
    return {
        "job_id": load_job.job_id,
        "table": table_ref,
        "rows": destination_table.num_rows,
        "status": "SUCCESS",
    }

def query_bigquery(query: str, max_results: int = 50):
    """
    Executes a SQL query in Google Cloud BigQuery and returns the results in a structured format.

    Args:
        query (str): Standard SQL query string to run against BigQuery.
        max_results (int): Maximum number of rows to return. Defaults to 50.
    """
    client = bigquery.Client(project=project)
    query_job = client.query(query)
    results = query_job.result(max_results=max_results)
    print('results', results)
    rows = []
    for row in results:
        row_dict = {}
        for key, value in row.items():
            if hasattr(value, "isoformat"):
                row_dict[key] = value.isoformat()
            elif isinstance(value, (int, float, bool, str)) or value is None:
                row_dict[key] = value
            else:
                row_dict[key] = str(value)
        rows.append(row_dict)

    columns = [field.name for field in results.schema] if results.schema else []

    return {
        "columns": columns,
        "total_rows": results.total_rows,
        "returned_rows": len(rows),
        "data": rows,
    }


