from google.adk.agents.llm_agent import Agent
from .tools import list_buckets, create_bucket, delete_bucket, load_csv_to_bq, query_bigquery

root_agent = Agent(
    model='gemini-3.5-flash',
    name='cloud_agent',
    description='A helpful Cloud support assistant for managing GCS buckets, loading data, and querying BigQuery tables.',
    instruction="""
    Answer user questions to the best of your knowledge.
    You have access to tools to:
    - List buckets
    - Create buckets with specified storage class and location
    - Delete buckets (always ask for user confirmation before deleting any bucket)
    - Load CSV files from a GCS bucket into a BigQuery table
    - Query BigQuery tables using standard SQL (query_bigquery)

    Formatting guidelines:
    - When returning query results, always format the response in clean Markdown tables with column headers.
    - If summarizing data, provide key metrics in bullet points along with the tabular data.
    - Keep SQL queries standard, robust, and properly formatted.
    """,
    tools=[list_buckets, create_bucket, delete_bucket, load_csv_to_bq, query_bigquery]
)