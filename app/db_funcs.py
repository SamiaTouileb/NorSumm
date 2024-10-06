import sqlite3


def create_database(database):
    with sqlite3.connect(database) as db:
        c = db.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS admins
                    (_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                     password TEXT NOT NULL);"""
        )
        c.execute(
            """
        CREATE TABLE IF NOT EXISTS summaries
        (article_id TEXT NOT NULL UNIQUE,
        summary_type TEXT NOT NULL,
        summary_id TEXT NOT NULL,
        preference_count INT,
        PRIMARY KEY (article_id, summary_type, summary_id));"""
        )
        try:
            c.execute(
                """
            INSERT INTO admins (username, password)
            VALUES (?, ?)
            """,
                # Not good practice, but works for this usecase
                ("norsum_admin", "norsum1234"),
            )
        except sqlite3.IntegrityError:
            pass
        db.commit()


def get_credentials(database, username):
    with sqlite3.connect(database) as db:
        db.row_factory = sqlite3.Row
        c = db.cursor()
        c.execute(
            f"""
        SELECT username, password FROM admins
        WHERE username='{username}'
        """
        )
        creds = c.fetchone()

    return creds


def get_all(database):
    with sqlite3.connect(database) as db:
        db.row_factory = sqlite3.Row
        c = db.cursor()
        c.execute("""SELECT * from summaries""")
        out = c.fetchall()
    for row in out:
        for k, v in dict(row).items():
            print(k, v)
        print()


def summary_db(database, article_id, summary_id, preference_type):
    with sqlite3.connect(database) as db:
        db.row_factory = sqlite3.Row
        c = db.cursor()
        statement = f"""
        SELECT * from summaries
        WHERE article_id='{article_id}' AND summary_type = '{preference_type}' AND summary_id = '{summary_id}';
        """

        insert_statement = f"""
        INSERT INTO summaries (article_id, summary_type, summary_id, preference_count)
        VALUES (?, ?, ?, ?)
        """
        c.execute(statement)
        out = c.fetchone()
        if out is None:
            try:
                c.execute(
                    insert_statement, (article_id, preference_type, summary_id, 1)
                )
            except sqlite3.IntegrityError:
                pass
        else:
            update_statement = f"""
            UPDATE summaries
            SET preference_count = {out["preference_count"] + 1}
            WHERE article_id='{article_id}' AND summary_type = '{preference_type}' AND summary_id = '{summary_id}';
            """
            c.execute(update_statement)
            print(out)
            for key, value in dict(out).items():
                print(key, value)
