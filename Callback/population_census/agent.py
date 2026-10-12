from google.adk.agents.llm_agent import Agent
import google.auth
from google.adk.integrations.bigquery import BigQueryToolset, BigQueryCredentialsConfig
from google.adk.integrations.bigquery.config import BigQueryToolConfig, WriteMode
from .tools import list_buckets, create_bucket, delete_bucket, load_csv_to_bq, query_bigquery
from .agent_callback import check_access, log_completion
from .model_callback import check_token_limit, modify_output, route_model_by_user
from .tool_callbacks import check_data_access, filter_data
credentails, project_id  = google.auth.default()


bigquery_tool_config = BigQueryToolConfig(write_mode=WriteMode.ALLOWED)

credentails_config = BigQueryCredentialsConfig(credentials=credentails)
bigquery_toolset = BigQueryToolset(credentials_config=credentails_config, bigquery_tool_config=bigquery_tool_config)


root_agent = Agent(
    model='gemini-3.5-flash',   
    name='population_census',
    description='A helpful assistant for population related questions',
    instruction= """Answer population related questions based on data available in Bigquery 
    table gcai-sep-26.Popluation_census.global_population.  

    Show data in bullet points/tabular format. Do not show sql query.
    if not related to population census then politely refuse and say that i can only answer population related questions""",
    # before_agent_callback=check_access,
    # after_agent_callback=log_completion,
    # before_model_callback=check_token_limit,
    # after_model_callback=modify_output,
    # model_routing_call/ack=route_model_by_user,
    before_tool_callback=check_data_access,
    after_tool_callback=filter_data
)
