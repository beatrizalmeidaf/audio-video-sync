import sqlite3
import os
import uuid
from datetime import datetime

DB_PATH = "jobs.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Criação da tabela de usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT UNIQUE,
                password_hash TEXT,
                created_at TEXT
            )
        ''')
        
        # Criação da tabela de jobs vinculada ao usuário
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                user_id TEXT,
                filename TEXT,
                status TEXT,
                progress REAL,
                text TEXT,
                created_at TEXT,
                download_url TEXT,
                error_message TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        conn.commit()

def create_user(name, email, password_hash):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        created_at = datetime.now().isoformat()
        user_id = str(uuid.uuid4())
        try:
            cursor.execute('''
                INSERT INTO users (id, name, email, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, name, email, password_hash, created_at))
            conn.commit()
            return user_id
        except sqlite3.IntegrityError:
            return None # Email já existe

def get_user_by_email(email):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_user_by_id(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def create_job(job_id, user_id, filename):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        created_at = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO jobs (job_id, user_id, filename, status, progress, text, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (job_id, user_id, filename, 'uploading', 0.0, 'Upload em andamento...', created_at))
        conn.commit()

def update_job_status(job_id, progress, text, status=None, download_url=None, error_message=None):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        updates = ["progress = ?", "text = ?"]
        params = [progress, text]
        
        if status is not None:
            updates.append("status = ?")
            params.append(status)
            
        if download_url is not None:
            updates.append("download_url = ?")
            params.append(download_url)
            
        if error_message is not None:
            updates.append("error_message = ?")
            params.append(error_message)
            
        updates_str = ", ".join(updates)
        params.append(job_id)
        
        cursor.execute(f"UPDATE jobs SET {updates_str} WHERE job_id = ?", tuple(params))
        conn.commit()

def get_job(job_id, user_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE job_id = ? AND user_id = ?", (job_id, user_id))
        row = cursor.fetchone()
        # Se usuário não tem esse job, retorna None.
        return dict(row) if row else None

def get_all_jobs(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        return [dict(row) for row in cursor.fetchall()]

def delete_job(job_id, user_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM jobs WHERE job_id = ? AND user_id = ?", (job_id, user_id))
        conn.commit()

def update_job_filename(job_id, user_id, new_filename):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE jobs SET filename = ? WHERE job_id = ? AND user_id = ?
        ''', (new_filename, job_id, user_id))
        conn.commit()
