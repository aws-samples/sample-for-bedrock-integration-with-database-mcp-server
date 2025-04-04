import boto3
import json
import os
import utility
import random
import time
import secrets
import math
import asyncio
from botocore.config import Config
from botocore.exceptions import ClientError


# This class manages interactions with AWS Bedrock models, handling model responses and tool executions.


class BedrockConverseAgent:
    def __init__(self, model_id):
        self.model_id = model_id
        session = boto3.Session()
        self.region = session.region_name

        # Configure retry strategy
        retry_config = Config(
            region_name=self.region,
            retries=dict(
                max_attempts=5,  # Number of retry attempts
                mode="adaptive",  # Adaptive or standard mode
                total_max_attempts=10,  # Including initial call
            ),
            # Optional: Add timeouts
            connect_timeout=5,  # Connection timeout in seconds
            read_timeout=60,  # Read timeout in seconds
            max_pool_connections=10,  # Max concurrent connections
        )

        self.client = boto3.client(
            "bedrock-runtime", region_name=self.region, config=retry_config
        )
        # Set default conversation parameters
        self.system_prompt = "You are a helpful assistant that can use tools to answer questions and perform tasks."
        self.messages = []  # Maintains conversation history
        self.tools = None  # Tool manager instance
        self.utility = None  # Utility helper instance

    async def invoke_prompt(self, prompt, utility):
        """
        Initiates a new conversation turn with the model.
        Args:
            prompt: User input text
            utility: Utility helper instance for tool management
        """
        content = [{"text": prompt}]
        self.utility = utility
        return await self.invoke(content)

    async def invoke(self, content):
        # print(f"User: {json.dumps(content, indent=4)}")
        self.messages.append({"role": "user", "content": content})
        response = await self._get_response()
        print(f"Agent: {json.dumps(response, indent=4)}")

        return await self._handle_response(response)

    # Calling Bedrock Converse API now

    async def _get_response(self):
        response = self.client.converse(
        modelId=self.model_id,
        messages=self.messages,
        system=[
            {
                "text": self.system_prompt
            }
        ],
        inferenceConfig={
            "maxTokens": 4096,
            "temperature": 0.6,
        },
        toolConfig=self.tools.get_tools()
        )
        return response


    """
    Use a stop reason parameter here to determine if a tool is being used or not. If it is being used,
    extract the details regarding the tool, otherwise just return the response.
    """

    async def _handle_response(self, response):
        self.messages.append(response["output"]["message"])
        print("\n----- Response Debugging -----")
        print(f"Stop Reason: {response.get('stopReason', 'No stop reason found')}")
        # print(f"Full Response Structure: {json.dumps(response, indent=2)}")

        stop_reason = response["stopReason"]
        print(f"\nProcessing stop reason: {stop_reason}")

        if stop_reason in ["end_turn", "stop_sequence"]:
            try:
                message = response.get("output", {}).get("message", {})
                content = message.get("content", [])
                text = content[0].get("text", "")
                return text
            except (KeyError, IndexError):
                return ""

        # Handle tool execution requests
        elif stop_reason == "tool_use":
            try:
                tool_response = []

                for item in response["output"]["message"]["content"]:
                    if "toolUse" in item:
                        tool_request = {
                            "toolUseId": item["toolUse"][
                                "toolUseId"
                            ],  # Unique ID for this tool use
                            "name": item["toolUse"]["name"],  # Name of the tool to use
                            "input": item["toolUse"][
                                "input"
                            ],  # Parameters for the tool
                        }

                        # Execute the tool and get result
                        tool_result = await self.tools.execute_tool(tool_request)
                        print(f"Inside tool_use:Tool Result: {tool_result}")
                        tool_response.append({"toolResult": tool_result})

                return await self.invoke(tool_response)

            except KeyError as e:
                raise ValueError(f"Missing required tool use field: {e}")

            except Exception as e:
                raise ValueError(f"Failed to execute tool because of: {e}")

        elif stop_reason == "max_tokens":
            await self.invoke_prompt("Please continue.")

        else:
            raise ValueError(f"Response stopped due to reason: {stop_reason}")
