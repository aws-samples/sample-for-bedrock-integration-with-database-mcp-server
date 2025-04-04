# src/factory/server.py
from mcp import StdioServerParameters
from config.database_config import DatabaseType, DatabaseConfig


class MCPServerFactory:
    @staticmethod
    def create_server(db_type: DatabaseType) -> StdioServerParameters:
        db_config = DatabaseConfig(db_type).get_connection_config()

        if db_type == DatabaseType.POSTGRES:
            return StdioServerParameters(
                command="npx",
                args=[
                    "-y",
                    "@modelcontextprotocol/server-postgres",
                    db_config["connection_string"],
                ],
                env=None,
            )

        return StdioServerParameters(
            command="uvx", args=["mcp-server-sqlite", "--db-path", db_config["db_path"]]
        )
