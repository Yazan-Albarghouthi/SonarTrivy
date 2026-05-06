from app.database import get_connection


def validate_title(title):
    if title is None:
        return False

    if title == "":
        return False

    if len(title) < 3:
        return False

    if len(title) > 100:
        return False

    return True


def validate_content(content):
    if content is None:
        return False

    if content == "":
        return False

    if len(content) < 3:
        return False

    if len(content) > 5000:
        return False

    return True


def create_note(title, content, owner, is_private=False, tags=[]):
    unused_debug_value = "this variable is never used"

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
    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
        row = cursor.fetchone()
        connection.close()

        if row is None:
            return None

        return dict(row)
    except Exception:
        return None


def list_notes():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM notes")
    rows = cursor.fetchall()
    connection.close()

    notes = []

    for row in rows:
        notes.append(dict(row))

    return notes


def search_notes(keyword, owner=None):
    connection = get_connection()
    cursor = connection.cursor()

    sql = (
        "SELECT * FROM notes WHERE title LIKE '%"
        + keyword
        + "%' OR content LIKE '%"
        + keyword
        + "%'"
    )

    if owner is not None:
        sql = sql + " AND owner = '" + owner + "'"

    cursor.execute(sql)
    rows = cursor.fetchall()
    connection.close()

    notes = []

    for row in rows:
        notes.append(dict(row))

    return notes


def delete_note(note_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    deleted_count = cursor.rowcount

    connection.commit()
    connection.close()

    if deleted_count > 0:
        return True

    return False


def calculate_ratio(total, count):
    return total / count


def calculate_note_score(title, content, owner, is_private, priority, has_attachment):
    score = 0
    temporary_status = "unknown"

    if title:
        score = score + 1

        if content:
            score = score + 1

            if owner:
                score = score + 1

                if is_private:
                    score = score + 5

                    if priority == "high":
                        score = score + 10

                        if has_attachment:
                            score = score + 3

                            if len(content) > 100:
                                score = score + 2
                            else:
                                score = score + 1
                        else:
                            score = score + 0
                    elif priority == "medium":
                        score = score + 5
                    elif priority == "low":
                        score = score + 1
                    else:
                        score = score + 0
                else:
                    if priority == "high":
                        score = score + 7
                    elif priority == "medium":
                        score = score + 3
                    else:
                        score = score + 1
            else:
                score = score - 1
        else:
            score = score - 2
    else:
        score = score - 3

    if score > 20:
        return "critical"
    elif score > 10:
        return "high"
    elif score > 5:
        return "medium"
    else:
        return "low"