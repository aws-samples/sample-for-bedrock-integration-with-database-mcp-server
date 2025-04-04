import asyncio
from mcp import StdioServerParameters
from agent import BedrockConverseAgent
from utility import UtilityHelper
from mcpclient import MCPClient
import os
import argparse
from config.database_config import DatabaseType
from factory.server import MCPServerFactory

"""
Database Chat Interface using Claude 3 or other LLM models available in Bedrock 
and Model Context Protocol (MCP). This sample implements a natural language interface 
for database interactions, leveraging Amazon Bedrock's Claude 3 model and MCP Server for database operations.
"""

# Constants
SYSTEM_PROMPT = """
You are an expert database assistant capable of:
1. Executing SQL queries
2. Analyzing database structures
3. Providing data insights
4. Helping with database operations
Please use available tools to assist with database-related tasks.
"""
# Configure Bedrock Model. Claude Sonnet is being used here.
# However, any other Bedrock supported models can be found
# here https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html
MODEL_ID = "us.anthropic.claude-3-5-sonnet-20240620-v1:0"


async def bedrock_database_chat(db_type: DatabaseType):
    """Main function to start the database chat interface"""
    # Initialize Bedrock Agent and Tools
    bedrock_agent = BedrockConverseAgent(MODEL_ID)
    utility_manager = UtilityHelper()
    bedrock_agent.tools = utility_manager

    # Set up system instructions for the AI
    bedrock_agent.system_prompt = SYSTEM_PROMPT

    # Create MCP server based on database type
    mcp_server_config = MCPServerFactory.create_server(db_type)

    # Start chat interface
    await start_chat_session(bedrock_agent, mcp_server_config, utility_manager)


async def start_chat_session(bedrock_agent, mcp_config, utility_manager):
    """Initialize and run the chat session with database interaction"""
    async with MCPClient(mcp_config) as mcp_client:
        # Register available database tools
        db_tools = await mcp_client.get_available_tools()
        await register_database_tools(utility_manager, db_tools, mcp_client)

        # Start interactive chat loop
        await handle_chat_interactions(bedrock_agent, utility_manager)


async def register_database_tools(utility_manager, db_tools, mcp_client):
    """Register available database tools with the tool manager"""
    for tool in db_tools:
        utility_manager.register_tool(
            name=tool.name,
            func=mcp_client.call_tool,
            description=tool.description,
            input_schema={"json": tool.inputSchema},
        )
        print(f"Registered database tool: {tool.name}")


async def handle_chat_interactions(bedrock_agent, utility_manager):
    """Handle user interactions in the chat session"""
    while True:
        try:
            user_input = input("\nEnter your database query in natural language: ")
            if user_input.lower() in ["bye", "quit", "q", "exit"]:
                print("\nEnding current chat session. Now Go Build...")
                break

            ai_response = await bedrock_agent.invoke_prompt(user_input, utility_manager)
            print(f"\nAI Assistant: {ai_response}")

        except KeyboardInterrupt:
            print("\nChat session terminated by user.")
            break
        except Exception as error:
            print(f"\nError during chat session: {error}")


def parse_arguments():
    parser = argparse.ArgumentParser(description="Database Chat Interface")
    parser.add_argument(
        "--db-type",
        type=str,
        choices=[db_type.value for db_type in DatabaseType],
        default=DatabaseType.SQLITE.value,
        help="Type of database to use (sqlite or postgres)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    db_type = DatabaseType(args.db_type)
    asyncio.run(bedrock_database_chat(db_type))
