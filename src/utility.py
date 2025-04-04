# This class integrates various AI tools with Amazon Bedrock, allowing for dynamic tool registration and execution within an AI-powered application.
import json


class UtilityHelper:
    # Name Mapping allows registering tools while maintaining Bedrock compatibility by removing hyphens
    def __init__(self):
        self._tools = {}
        self._name_mapping = {}

    # _correct_name method replaces hyphens with underscores in tool names for compatibility with Bedrock.

    @staticmethod
    def _correct_name(name):
        return name.replace("-", "_")

    # This function registers a new tool with the system while correcting the name to Bedrock standards
    def register_tool(self, name, func, description, input_schema):
        corrected_name = UtilityHelper._correct_name(name)
        self._name_mapping[corrected_name] = name
        self._tools[corrected_name] = {
            "function": func,
            "description": description,
            "input_schema": input_schema,
            "original_name": name,
        }

    def get_tools(self):
        tool_specs = []
        for corrected_name, tool in self._tools.items():
            tool_specs.append(
                {
                    "toolSpec": {
                        "name": corrected_name,
                        "description": tool["description"],
                        "inputSchema": tool["input_schema"],
                    }
                }
            )

        return {"tools": tool_specs}

    async def execute_tool(self, payload):
        tool_use_id = payload["toolUseId"]
        corrected_name = payload["name"]
        tool_input = payload["input"]

        if corrected_name not in self._tools:
            raise ValueError(f"Unknown tool {corrected_name} not found")

        try:
            tool_func = self._tools[corrected_name]["function"]
            original_name = self._tools[corrected_name]["original_name"]
            result = await tool_func(original_name, tool_input)

            return {
                "toolUseId": tool_use_id,
                "content": [{"text": str(result)}],
                "status": "success",
            }

        except Exception as e:
            return {
                "toolUseId": tool_use_id,
                "content": [{"text": f"Error executing tool: {str(e)}"}],
                "status": "error",
            }

    def clear_tools(self):
        self._tools.clear()
