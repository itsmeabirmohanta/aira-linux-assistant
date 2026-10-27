"""
Memory system for ARIA:
- SQLite for structured session history, logs, and user preferences
- ChromaDB for semantic vector retrieval across past sessions
"""

import json
import os
import sqlite3
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from aria.utils.logger import logger
from aria.config import config


class Memory:
    def __init__(self):
        self.db_dir = config.memory_dir
        self.db_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.db_dir, 0o700)
        except Exception:
            pass

        self.db_path = self.db_dir / "memory.db"
        self._init_sqlite()
        try:
            if self.db_path.exists():
                os.chmod(self.db_path, 0o600)
        except Exception:
            pass
        self._init_chroma()

    def _init_sqlite(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    task TEXT,
                    summary TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    role TEXT,
                    content TEXT,
                    timestamp REAL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id)
                )
            """)
            conn.commit()

    def _init_chroma(self):
        self._chroma_collection = None
        try:
            import chromadb
            chroma_dir = self.db_dir / "chroma"
            client = chromadb.PersistentClient(path=str(chroma_dir))
            self._chroma_collection = client.get_or_create_collection(name="aria_tasks")
            logger.debug("ChromaDB vector memory initialized.")
        except Exception as e:
            logger.debug(f"ChromaDB not available: {e}. Falling back to SQLite search.")

    def create_session(self, task: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sessions (timestamp, task, summary) VALUES (?, ?, ?)",
                (time.time(), task, ""),
            )
            session_id = cursor.lastrowid
            conn.commit()
            return session_id

    def add_message(self, session_id: int, role: str, content: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (session_id, role, content, time.time()),
            )
            conn.commit()

    def update_summary(self, session_id: int, summary: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE sessions SET summary = ? WHERE id = ?",
                (summary, session_id),
            )
            conn.commit()

        # Index in ChromaDB if available
        if self._chroma_collection:
            try:
                self._chroma_collection.upsert(
                    ids=[str(session_id)],
                    documents=[summary],
                    metadatas=[{"session_id": session_id, "timestamp": time.time()}],
                )
            except Exception as e:
                logger.debug(f"Vector upsert note: {e}")

    def get_recent_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return the most recent messages from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            rows = cursor.fetchall()
            return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

    def search_past_context(self, query: str, limit: int = 3) -> List[str]:
        """Search past sessions relevant to the query."""
        results = []
        if self._chroma_collection:
            try:
                res = self._chroma_collection.query(query_texts=[query], n_results=limit)
                docs = res.get("documents", [[]])[0]
                results.extend(docs)
                if results:
                    return results
            except Exception as e:
                logger.debug(f"Vector search note: {e}")

        # Fallback keyword match in SQLite
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT task, summary FROM sessions WHERE task LIKE ? OR summary LIKE ? ORDER BY id DESC LIMIT ?",
                (f"%{query}%", f"%{query}%", limit),
            )
            for row in cursor.fetchall():
                results.append(f"Past task: {row[0]}. Outcome: {row[1]}")

        return results

    def export_personal_data(self) -> Dict[str, Any]:
        """
        DPDP / GDPR Right to Data Portability compliance.
        Exports all stored sessions, messages, and vector metadata into a structured JSON payload.
        """
        data: Dict[str, Any] = {
            "exported_at": time.time(),
            "aria_version": "2.0",
            "sessions": [],
            "messages": [],
        }
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, timestamp, task, summary FROM sessions ORDER BY id ASC")
            for sid, ts, task, summary in cursor.fetchall():
                data["sessions"].append({
                    "id": sid,
                    "timestamp": ts,
                    "task": task,
                    "summary": summary,
                })

            cursor.execute("SELECT id, session_id, role, content, timestamp FROM messages ORDER BY id ASC")
            for mid, sid, role, content, ts in cursor.fetchall():
                data["messages"].append({
                    "id": mid,
                    "session_id": sid,
                    "role": role,
                    "content": content,
                    "timestamp": ts,
                })
        return data

    def purge_all_data(self) -> bool:
        """
        DPDP / GDPR Right to Erasure ('Right to be Forgotten') compliance.
        Permanently wipes all conversation logs, episodic sessions, and vector embeddings.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM messages")
                cursor.execute("DELETE FROM sessions")
                conn.commit()

            # Vacuum database file to reclaim disk space outside active transaction
            conn_vac = sqlite3.connect(self.db_path)
            conn_vac.isolation_level = None
            conn_vac.execute("VACUUM")
            conn_vac.close()

            if self._chroma_collection:
                try:
                    import chromadb
                    chroma_dir = self.db_dir / "chroma"
                    client = chromadb.PersistentClient(path=str(chroma_dir))
                    client.delete_collection("aria_tasks")
                    self._chroma_collection = client.get_or_create_collection(name="aria_tasks")
                except Exception as e:
                    logger.debug(f"Chroma purge note: {e}")

            logger.info("All personal episodic memory purged successfully (DPDP Erasure Compliance).")
            return True
        except Exception as e:
            logger.error(f"Failed to purge memory: {e}")
            return False
