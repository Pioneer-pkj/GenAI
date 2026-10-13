from google.adk.agents.llm_agent import Agent
import google.auth
from google.adk.apps import App
from google.adk.integrations.bigquery import BigQueryToolset, BigQueryCredentialsConfig
from google.adk.integrations.bigquery.config import BigQueryToolConfig, WriteMode
from google.adk.plugins.logging_plugin import LoggingPlugin
from google.adk.plugins.bigquery_agent_analytics_plugin import BigQueryAgentAnalyticsPlugin
from .agent_callback import check_access, log_completion


credentails, project_id  = google.auth.default()    


bigquery_tool_config = BigQueryToolConfig(write_mode=WriteMode.ALLOWED)

logging_plugin = LoggingPlugin(name='population_census_plugin')
bq_plugin = BigQueryAgentAnalyticsPlugin(project_id='gcai-sep-26', dataset_id='Popluation_census')


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
    tools=[bigquery_toolset],
    before_agent_callback=check_access,
    after_agent_callback=log_completion
)

app = App(
    name="population_census",
    root_agent=root_agent,
    plugins=[logging_plugin, bq_plugin]
    )