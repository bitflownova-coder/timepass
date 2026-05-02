import os
import re
import sqlite3


def _normalize(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', (text or '').lower())


def _is_bitflow_match(original_filename: str | None,
                       text_preview: str | None,
                       extracted_text: str | None,
                       user_folder: str | None,
                       predicted_label: str | None) -> bool:
    combined = ' '.join(filter(None, [original_filename, text_preview, extracted_text]))
    if 'bitflow' in _normalize(combined):
        return True

    folder = (user_folder or '').strip().lower()
    predicted = (predicted_label or '').strip().lower()
    legacy = {'our', 'complete', 'bitflow files', 'bitflow file', 'bitflow'}
    return folder in legacy or predicted in legacy


def main() -> int:
    db_path = os.path.join('instance', 'app.db')
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return 1

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, original_filename, extracted_text, text_preview,
               user_folder, predicted_label, deleted_at
        FROM document
        """
    )

    rows = cur.fetchall()
    updated = 0
    for doc_id, original_filename, extracted_text, text_preview, user_folder, predicted_label, deleted_at in rows:
        if deleted_at is not None:
            continue
        if _is_bitflow_match(original_filename, text_preview, extracted_text, user_folder, predicted_label):
            cur.execute(
                """
                UPDATE document
                SET user_folder = ?, predicted_label = ?, suggested_folder = ?
                WHERE id = ?
                """,
                ('Bitflow', 'Bitflow', 'Bitflow', doc_id)
            )
            updated += 1

    conn.commit()
    conn.close()

    print(f"Bitflow merge complete. Updated {updated} document(s).")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
