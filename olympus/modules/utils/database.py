import sqlite3
from typing import Any, List, Optional, Tuple, Union
 
from .. import kronos
 
class DBManager:
    """
    A utility class to manage SQLite database connections and queries
    """
 
    def __init__(self, logger: kronos.Logger):
        """
        Initialize the DBManager class
 
        Args:
            logger: The logger instance
        """
        self._logger = logger
        self._conn = None
       
        self._logger.info(f"DBManager initialized")
 
    def connect(self, path: Optional[str] = "../../database/data.db") -> None:
        """
        Establish a connection to the SQLite database
 
        Args:
            path: The path to the local SQLite DB
       
        Raises:
            Exception: On connection fail
        """
        try:
            self._conn = sqlite3.connect(path)
            self._logger.info("Connected to SQLite DB")
            self._logger.debug(f"SQLite DB located at {path}")
        except Exception as e:
            self._logger.exception(f"Error connecting to SQLite DB at path {path}: {e}")
            raise Exception("Failed to connect to SQLite DB")
 
    def close(self) -> None:
        """
        Close the database connection
        """
        if self._conn:
            self._conn.close()
            self._conn = None
            self._logger.info(f"SQLite DB connection closed")
 
    def execute_query(self, query: str, params: Optional[Union[Tuple, List]] = None) -> None:
        """
        Execute a query that does not return results
 
        Args:
            query: The query to be executed
            params: The optional paramethers for the query
       
        Raises:
            Exception: On query execution fail
        """
        if not self._conn:
            self._logger.error("Tried to execute a query without any connection")
            raise Exception("Invalid query call")
       
        allowed_commands = ("CREATE", "DROP", "ALTER", "INSERT", "UPDATE", "DELETE", "REPLACE", "BEGIN", "COMMIT", "ROLLBACK")
        tmp_query = query.strip().upper()
        if not tmp_query.startswith(allowed_commands):
            self._logger.error("Invalid command sent to query execution")
            raise Exception("Invalid command at query execution")
       
        self._logger.debug(f"Executing query", {"query": query, "params": params})
 
        try:
            cursor = self._conn.cursor()
            cursor.execute(query, params or ())
 
            self._conn.commit()
            self._logger.debug(f"Query modified {cursor.rowcount} row(s)")
        except Exception as e:
            self._logger.exception(f"Error during query execution: {e}")
            self._conn.rollback()
            raise Exception("Error during query execution")
 
    def fetch_query(self, query: str, params: Optional[Union[Tuple, List]] = None) -> List[Tuple[Any]]:
        """
        Execute a SELECT query and return the results
 
        Args:
            query: The query to be executed
            params: The optional paramethers for the query
       
        Returns:
            List of Tuples for the results
       
        Raises:
            Exception: On query fetching fail
        """
        if not self._conn:
            self._logger.error("Tried to fetch a query without any connection")
            raise Exception("Invalid query call")
       
        allowed_commands = ("SELECT", "PRAGMA", "EXPLAIN", "VALUES")
        tmp_query = query.strip().upper()
        if not tmp_query.startswith(allowed_commands):
            self._logger.error("Invalid command sent to query fetching")
            raise Exception("Invalid command at query fetching")
 
        self._logger.debug(f"Fetching query", {"query": query, "params": params})
 
        try:
            cursor = self._conn.cursor()
            cursor.execute(query, params or ())
            results = cursor.fetchall()
 
            self._logger.debug(f"Query returned {len(results)} row(s)")
            return results
        except Exception as e:
            print(f"Error during query fetching: {e}")
            raise Exception("Error during query fetching")
 
    def execute_script(self, script: str) -> None:
        """
        Execute a script containing multiple SQL statements
 
        Args:
            script: The script to be executed
       
        Raises:
            Exception: On execution fail
        """
        if not self._conn:
            self._logger.error("Tried to fetch a query without any connection")
            raise Exception("Invalid query call")
       
        self._logger.debug(f"Executing script with {len(script.splitlines())} row(s)", {"script": script})
 
        try:
            cursor = self._conn.cursor()
            cursor.executescript(script)
            self._conn.commit()
            self._logger.debug(f"Query modified {cursor.rowcount} row(s)")
        except Exception as e:
            self._logger.exception(f"Error during script execution: {e}")
            self._conn.rollback()
            raise Exception("Error during script execution")
 
    def __enter__(self):
        """Context manager support"""
        self.connect()
        return self
 
    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit - no explicit release needed"""
        self.close()
