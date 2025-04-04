# src/config/database_config.py
from enum import Enum
import os
from configparser import ConfigParser


class DatabaseType(Enum):
    SQLITE = "sqlite"
    POSTGRES = "postgres"


class DatabaseConfig:
    def __init__(self, db_type: DatabaseType):
        self.db_type = db_type
        
    def get_connection_config(self):
        if self.db_type == DatabaseType.POSTGRES:
            return self._get_postgres_config()
        return self._get_sqlite_config()

    def _get_postgres_config(self):
        db_config = _read_config()
        return {
            "type": "postgres",
            "connection_string": (
                f"postgresql://{db_config['user']}:{db_config['password']}"
                f"@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"
                f"?sslmode=verify-full&sslrootcert={db_config['ssl_cert_path']}"
            ),
        }

    def _read_config(self, filename="dbconfig.ini", section="rdspostgresql"):
        parser = ConfigParser()
        parser.read(filename)

        database_config = {}

        if parser.has_section(section):
            parameters = parser.items(section)
            for param in parameters:
                database_config[param[0]] = param[1]
        else:
            raise Exception(
                f"The section {section} referred is not found in the {filename} file configured for database details"
            )

        return database_config

    def _get_sqlite_config(self):
        # Get the project's root directory path
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Construct path to the database in the data folder
        default_db_path = os.path.join(project_root, 'data', 'mymcpdb.db')
        
        return {
            "type": "sqlite",
            "db_path": os.getenv("SQLITE_DB_PATH", default_db_path),
        }

