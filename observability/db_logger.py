import sqlite3
import json
import os
from typing import List, Dict, Any
from app.config import settings

class SQLiteLogger:
    """
    Handles logging of system metrics, inputs, and outputs to an SQLite database.
    Stores query text, retrieved contexts, generation results, and processing latencies.
    """
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.SQLITE_DB_PATH
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.db_path) or "data", exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Creates the query_logs table if it does not already exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                retrieved_chunks TEXT NOT NULL, -- JSON serialized string
                response TEXT NOT NULL,
                latency_ms INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def log_query(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        response: str,
        latency_ms: int
    ) -> int:
        """
        Inserts a query log entry into the database.
        Returns:
            The primary key (id) of the inserted row.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            chunks_json = json.dumps(retrieved_chunks)
            cursor.execute(
                """
                INSERT INTO query_logs (query, retrieved_chunks, response, latency_ms)
                VALUES (?, ?, ?, ?)
                """,
                (query, chunks_json, response, latency_ms)
            )
            conn.commit()
            log_id = cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to log query telemetry to SQLite: {e}")
        finally:
            conn.close()
        return log_id

    def get_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves the latest query log entries."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id, query, retrieved_chunks, response, latency_ms, timestamp "
                "FROM query_logs ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            logs = []
            for row in rows:
                logs.append({
                    "id": row["id"],
                    "query": row["query"],
                    "retrieved_chunks": json.loads(row["retrieved_chunks"]),
                    "response": row["response"],
                    "latency_ms": row["latency_ms"],
                    "timestamp": row["timestamp"]
                })
            return logs
        finally:
            conn.close()
            
    def get_average_latency(self) -> float:
        """Returns the average latency of all queries stored in logs."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT AVG(latency_ms) FROM query_logs")
            avg = cursor.fetchone()[0]
            return float(avg) if avg is not None else 0.0
        finally:
            conn.close()
            
    def clear_logs(self):
        """Clears all entries in the logs table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM query_logs")
        conn.commit()
        conn.close()
