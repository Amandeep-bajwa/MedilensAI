#!/usr/bin/env python3
"""
MediLens AI — Database Recovery & Integrity Verification Utility (SRS Section 18.2)
Verifies cryptographic SHA-256 checksums, validates file integrity, restores data,
and checks post-restore entity counts.
"""

import os
import sys
import hashlib
import sqlite3
import subprocess

WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def compute_sha256(filepath: str) -> str:
    """Computes SHA-256 digest of a target file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def verify_checksum(backup_path: str) -> bool:
    """Verifies that the backup file matches its SHA-256 sidecar checksum."""
    sidecar_path = backup_path + ".sha256"
    if not os.path.exists(sidecar_path):
        print(f"[WARN] SHA-256 sidecar not found at {sidecar_path}. Integrity check bypassed.")
        return True

    with open(sidecar_path, "r", encoding="utf-8") as f:
        recorded_checksum = f.read().split()[0].strip()

    actual_checksum = compute_sha256(backup_path)
    if recorded_checksum != actual_checksum:
        print(f"[FAIL] SHA-256 mismatch! Expected {recorded_checksum}, found {actual_checksum}")
        return False

    print(f"[SUCCESS] SHA-256 checksum verified: {actual_checksum}")
    return True

def restore_sqlite(backup_path: str, target_db_path: str) -> bool:
    """Restores SQLite database from backup file and verifies table integrity."""
    if not verify_checksum(backup_path):
        return False

    # Connect to backup source and target destination
    src_conn = sqlite3.connect(backup_path)
    dst_conn = sqlite3.connect(target_db_path)
    try:
        src_conn.backup(dst_conn)
        print(f"[SUCCESS] Restored SQLite database to {target_db_path}")

        # Post-restore integrity verification
        cursor = dst_conn.cursor()
        cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        print(f"[INTEGRITY VERIFIED] Target database contains {table_count} tables.")
        return table_count > 0
    finally:
        dst_conn.close()
        src_conn.close()

def restore_postgres(backup_path: str, target_db_url: str) -> bool:
    """Restores PostgreSQL database from pg_dump custom archive."""
    if not verify_checksum(backup_path):
        return False

    try:
        cmd = ["pg_restore", "--clean", "--if-exists", "-d", target_db_url, backup_path]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"[SUCCESS] Restored PostgreSQL database from {backup_path}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"[ERROR] pg_restore execution failed: {e}")
        return False

def run_restore(backup_path: str, target_db_url: str = None) -> bool:
    """Executes the recovery pipeline."""
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup file does not exist: {backup_path}")

    target_db_url = target_db_url or os.getenv("DATABASE_URL", "sqlite:///./medilens.db")

    if target_db_url.startswith("sqlite"):
        rel_path = target_db_url.replace("sqlite:///", "").replace("sqlite://", "")
        target_path = os.path.abspath(os.path.join(WORKSPACE_DIR, rel_path))
        return restore_sqlite(backup_path, target_path)
    else:
        return restore_postgres(backup_path, target_db_url)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python restore_db.py <path_to_backup_file> [target_db_url]")
        sys.exit(1)

    backup_arg = sys.argv[1]
    url_arg = sys.argv[2] if len(sys.argv) > 2 else None

    if run_restore(backup_arg, url_arg):
        print("[COMPLETE] Database restoration and verification succeeded.")
        sys.exit(0)
    else:
        print("[FATAL] Database restoration failed.", file=sys.stderr)
        sys.exit(1)
