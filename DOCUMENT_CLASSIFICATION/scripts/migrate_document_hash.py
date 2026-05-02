import os
import sqlite3
import sys


def main() -> int:
    db_path = os.path.join('instance', 'app.db')
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return 1

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    row = cur.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='document'"
    ).fetchone()
    if not row or not row[0]:
        print("Document table not found")
        return 1

    schema_sql = row[0]
    if 'UNIQUE (user_id, file_hash)' in schema_sql:
        print("Migration already applied")
        return 0

    cur.execute('PRAGMA foreign_keys=off;')
    cur.execute('BEGIN;')

    cur.execute(
        """
        CREATE TABLE document_new (
            id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            filename VARCHAR(255) NOT NULL,
            original_filename VARCHAR(255) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            file_size INTEGER NOT NULL,
            file_hash VARCHAR(256) NOT NULL,
            mime_type VARCHAR(100),
            predicted_label VARCHAR(100),
            confidence_score FLOAT,
            suggested_folder VARCHAR(255),
            user_folder VARCHAR(255),
            extracted_text TEXT,
            text_preview VARCHAR(500),
            tags VARCHAR(500),
            is_encrypted BOOLEAN,
            is_duplicate BOOLEAN,
            duplicate_of INTEGER,
            uploaded_at DATETIME NOT NULL,
            processed_at DATETIME,
            accessed_at DATETIME,
            deleted_at DATETIME,
            PRIMARY KEY (id),
            FOREIGN KEY(user_id) REFERENCES user (id),
            FOREIGN KEY(duplicate_of) REFERENCES document (id),
            UNIQUE (user_id, file_hash)
        )
        """
    )

    cur.execute(
        """
        INSERT INTO document_new (
            id, user_id, filename, original_filename, file_path, file_size,
            file_hash, mime_type, predicted_label, confidence_score,
            suggested_folder, user_folder, extracted_text, text_preview, tags,
            is_encrypted, is_duplicate, duplicate_of, uploaded_at, processed_at,
            accessed_at, deleted_at
        )
        SELECT
            id, user_id, filename, original_filename, file_path, file_size,
            file_hash, mime_type, predicted_label, confidence_score,
            suggested_folder, user_folder, extracted_text, text_preview, tags,
            is_encrypted, is_duplicate, duplicate_of, uploaded_at, processed_at,
            accessed_at, deleted_at
        FROM document
        """
    )

    cur.execute('DROP TABLE document;')
    cur.execute('ALTER TABLE document_new RENAME TO document;')

    cur.execute('CREATE INDEX IF NOT EXISTS ix_document_user_id ON document (user_id);')
    cur.execute('CREATE INDEX IF NOT EXISTS ix_document_file_hash ON document (file_hash);')
    cur.execute('CREATE INDEX IF NOT EXISTS ix_document_uploaded_at ON document (uploaded_at);')

    cur.execute('COMMIT;')
    cur.execute('PRAGMA foreign_keys=on;')
    conn.commit()
    conn.close()

    print('Migration complete')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
