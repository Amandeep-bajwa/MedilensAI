#!/usr/bin/env python3
"""
MediLens AI — Automated Database Backup Utility (SRS Section 18.1)
Executes atomic database snapshots, calculates cryptographic SHA-256 checksums,
and applies retention pruning.
"""

import os
import sys
import time
import shutil
import hashlib
import sqlite3
import subprocess
from datetime import datetime

# Root workspace resolution
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKUP_DIR = os.path.join(WORKSPACE_DIR, "backups")

def compute_sha256(filepath: str) -> str:
    """Computes SHA-256 digest of a backup file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def backup_sqlite(source_path: str, destination_path: str) -> bool:
    """Executes atomic SQLite online backup using SQLite backup API."""
    if not os.path.exists(source_path):
        print(f"[ERROR] Source database not found: {source_path}")
        return False

    source_conn = sqlite3.connect(source_path)
    dest_conn = sqlite3.connect(destination_path)
    try:
        source_conn.backup(dest_conn)
        print(f"[SUCCESS] Atomic SQLite backup written to {destination_path}")
        return True
    finally:
        dest_conn.close()
        source_conn.close()

def backup_postgres(db_url: str, destination_path: str) -> bool:
    """Executes pg_dump for PostgreSQL deployments."""
    try:
        cmd = ["pg_dump", db_url, "-F", "c", "-f", destination_path]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"[SUCCESS] PostgreSQL pg_dump written to {destination_path}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"[ERROR] pg_dump execution failed: {e}")
        return False

def prune_old_backups(backup_dir: str, retention_days: int = 7):
    """Prunes backups older than the retention threshold."""
    cutoff = time.time() - (retention_days * 86400)
    for fname in os.listdir(backup_dir):
        fpath = os.path.join(backup_dir, fname)
        if os.path.isfile(fpath) and os.path.getmtime(fpath) < cutoff:
            os.remove(fpath)
            print(f"[PRUNED] Removed expired backup: {fname}")

def run_backup(retention_days: int = 7) -> str:
    """Executes the backup pipeline and returns the created backup filepath."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Read DATABASE_URL or default to SQLite
    db_url = os.getenv("DATABASE_URL", "sqlite:///./medilens.db")

    if db_url.startswith("sqlite"):
        rel_path = db_url.replace("sqlite:///", "").replace("sqlite://", "")
        abs_db_path = os.path.abspath(os.path.join(WORKSPACE_DIR, rel_path))
        backup_filename = f"medilens_backup_{timestamp}.db"
        dest_path = os.path.join(BACKUP_DIR, backup_filename)
        success = backup_sqlite(abs_db_path, dest_path)
    else:
        backup_filename = f"medilens_pg_backup_{timestamp}.dump"
        dest_path = os.path.join(BACKUP_DIR, backup_filename)
        success = backup_postgres(db_url, dest_path)

    if not success:
        raise RuntimeError("Database backup failed.")

    # Calculate SHA-256 checksum and write to sidecar file
    checksum = compute_sha256(dest_path)
    checksum_path = dest_path + ".sha256"
    with open(checksum_path, "w", encoding="utf-8") as f:
        f.write(f"{checksum}  {backup_filename}\n")

    print(f"[SHA-256] {checksum}")
    print(f"[INTEGRITY] Verified sidecar saved to {checksum_path}")

    # Prune expired backups
    prune_old_backups(BACKUP_DIR, retention_days)
    return dest_path

if __name__ == "__main__":
    try:
        created_file = run_backup()
        print(f"[COMPLETE] Database backup finished successfully: {created_file}")
    except Exception as exc:
        print(f"[FATAL] Backup aborted: {exc}", file=sys.stderr)
        sys.exit(1)
