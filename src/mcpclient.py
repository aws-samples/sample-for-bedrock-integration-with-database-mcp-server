from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClient:
    """
    Model Context Protocol (MCP) client implementation.
    Handles connection and interaction with MCP server for tool management
    and execution.
    """
    def __init__(self, server_params: StdioServerParameters):
        # Initialize client attributes
        self.read = None          # Stream reader
        self.write = None         # Stream writer
        self.server_params = server_params  # Database Server configuration
        self.session = None       # MCP session
        self._client = None       # Internal client instance

    async def __aenter__(self):
        """Async context manager entry point. Establishes connection."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit. Ensures proper cleanup of resources.
        Handles both session and client cleanup.
        """
        if self.session:
            await self.session.__aexit__(exc_type, exc_val, exc_tb)
        if self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)

    async def connect(self):
        """
        Establishes connection to MCP server.
        Sets up stdio client, initializes read/write streams,
        and creates client session.
        """
        # Initialize stdio client with server parameters
        self._client = stdio_client(self.server_params)
        
        # Get read/write streams
        self.read, self.write = await self._client.__aenter__()
        
        # Create and initialize session
        session = ClientSession(self.read, self.write)
        self.session = await session.__aenter__()
        await self.session.initialize()

    async def get_available_tools(self):
        """
        Retrieves and validates available tools from MCP server.
        
        Returns:
            list: Available tools with their configurations
            
        Raises:
            RuntimeError: If not connected to MCP server
        """
        # Verify session exists
        if not self.session:
            raise RuntimeError("Not connected to the MCP server.")

        # Get tools from server
        response = await self.session.list_tools()
        tools = response.tools

        # Log tool information for debugging
        # print(f"Tools type: {type(tools)}")
        # print(f"Tools content: {tools}")

        # Display available tools
        print(f"Found {len(tools)} tools:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")
        
        print("*** Completed listing of tools ***")
        return tools

    async def call_tool(self, tool_name, arguments):
        """
        Executes a specific tool with provided arguments.
        
        Args:
            tool_name (str): Name of the tool to execute
            arguments (dict): Tool-specific arguments
            
        Returns:
            dict: Tool execution results
            
        Raises:
            RuntimeError: If not connected to MCP server
        """
        # Verify session exists
        if not self.session:
            raise RuntimeError("Not connected to the MCP Server")

        # Execute tool and return results
        result = await self.session.call_tool(tool_name, arguments=arguments)
        return result
