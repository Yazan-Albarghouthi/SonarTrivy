from app.database import get_connection


def validate_title(title):
    return isinstance(title, str) and 3 <= len(title) <= 100


def validate_content(content):
    return isinstance(content, str) and 3 <= len(content) <= 5000


def create_note(title, content, owner, is_private=False, tags=None):
    if tags is None:
        tags = []

    if not validate_title(title):
        raise ValueError("Invalid title")

    if not validate_content(content):
        raise ValueError("Invalid content")

    tags.append("created")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "INSERT INTO notes (title, content, owner, is_private) VALUES (?, ?, ?, ?)",
        (title, content, owner, int(is_private)),
    )

    connection.commit()
    note_id = cursor.lastrowid
    connection.close()

    return get_note_by_id(note_id)


def get_note_by_id(note_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    row = cursor.fetchone()
    connection.close()

    if row is None:
        return None

    return dict(row)


def list_notes():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM notes")
    rows = cursor.fetchall()
    connection.close()

    return [dict(row) for row in rows]


def search_notes(keyword, owner=None):
    connection = get_connection()
    cursor = connection.cursor()

    pattern = f"%{keyword}%"

    if owner is not None:
        cursor.execute(
            "SELECT * FROM notes WHERE (title LIKE ? OR content LIKE ?) AND owner = ?",
            (pattern, pattern, owner),
        )
    else:
        cursor.execute(
            "SELECT * FROM notes WHERE title LIKE ? OR content LIKE ?",
            (pattern, pattern),
        )

    rows = cursor.fetchall()
    connection.close()

    return [dict(row) for row in rows]


def delete_note(note_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    deleted_count = cursor.rowcount

    connection.commit()
    connection.close()

    return deleted_count > 0


def calculate_ratio(total, count):
    if count == 0:
        raise ValueError("Count cannot be zero")
    return total / count


def _base_score(title, content, owner):
    if not title:
        return -3
    if not content:
        return -1
    if not owner:
        return 0
    return 3


def _priority_bonus(priority, has_attachment, content, is_private):
    if not is_private:
        return {"high": 7, "medium": 3}.get(priority, 1)
    bonus = 5
    if priority == "high":
        bonus += 10 + (3 if has_attachment else 0)
        bonus += 2 if len(content) > 100 else 1
    elif priority == "medium":
        bonus += 5
    elif priority == "low":
        bonus += 1
    return bonus


def _score_label(score):
    if score > 20:
        return "critical"
    if score > 10:
        return "high"
    if score > 5:
        return "medium"
    return "low"


def calculate_note_score(title, content, owner, is_private, priority, has_attachment):
    score = _base_score(title, content, owner)
    score += _priority_bonus(priority, has_attachment, content, is_private)
    return _score_label(score)
