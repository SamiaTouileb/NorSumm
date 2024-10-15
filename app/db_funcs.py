import sqlite3

from utils import _update


def create_database(database):
    with sqlite3.connect(database) as db:
        c = db.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS admins
            (
            _id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
            );"""
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS summaries
            (
            article_id TEXT NOT NULL,
            summary_type TEXT NOT NULL,
            summary_id TEXT NOT NULL,
            model TEXT,
            prompt TEXT,
            preference_count INT DEFAULT 0,
            PRIMARY KEY (article_id, summary_type, summary_id)
            );"""
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS age_groups
            (
            "18-24" INT DEFAULT 0,
            "25-34" INT DEFAULT 0,
            "35-44" INT DEFAULT 0,
            "45-54" INT DEFAULT 0,
            "55-64" INT DEFAULT 0,
            "65+" INT DEFAULT 0,
            article_id TEXT NOT NULL REFERENCES summaries(article_id),
            summary_type TEXT NOT NULL REFERENCES summaries(summary_type),
            summary_id TEXT NOT NULL REFERENCES summaries(summary_id),
            PRIMARY KEY (article_id, summary_type, summary_id)
            );
            """
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


def fetch_summaries_json(database):
    with sqlite3.connect(database) as db:
        db.row_factory = sqlite3.Row
        c = db.cursor()
        c.execute(
            """
            SELECT *
            FROM summaries as s
            INNER JOIN age_groups as a
            ON s.article_id = a.article_id
            AND s.summary_type = a.summary_type
            AND s.summary_id = a.summary_id
        """
        )
        out = c.fetchall()

    out_json = {}
    for summ in out:
        out_json = _update(
            out_json,
            {
                summ["article_id"]: {
                    summ["summary_type"]: {
                        summ["summary_id"]: {
                            "count": summ["preference_count"],
                            "model": summ["model"],
                            "prompt": summ["prompt"],
                            "age_groups": {
                                "18-24": summ["18-24"],
                                "25-34": summ["25-34"],
                                "35-44": summ["35-44"],
                                "45-54": summ["45-54"],
                                "55-64": summ["55-64"],
                                "65+": summ["65+"],
                            },
                        },
                    }
                }
            },
        )

    return out_json


def summary_db(database, article_id, preference_type, summary, age_group):
    # TODO: Clean up this messy code
    with sqlite3.connect(database) as db:
        db.row_factory = sqlite3.Row
        c = db.cursor()

        summary_select = f"""
        SELECT * from summaries
        WHERE article_id='{article_id}' AND summary_type = '{preference_type}' AND summary_id = '{summary["id"]}';
        """

        age_select = f"""
        SELECT * from age_groups
        WHERE article_id='{article_id}' AND summary_type = '{preference_type}' AND summary_id = '{summary["id"]}';
        """

        insert_statement = """
        INSERT INTO summaries (article_id, summary_type, summary_id, model, prompt, preference_count)
        VALUES (?, ?, ?, ?, ?, ?)
        """

        age_group_insert = f"""
        INSERT INTO age_groups(article_id, summary_type, summary_id, "{age_group}")
        VALUES (?, ?, ?, ?)
        """
        c.execute(summary_select)
        out = c.fetchone()
        if out is None:
            c.execute(
                insert_statement,
                (
                    article_id,
                    preference_type,
                    summary["id"],
                    summary["model"] if summary["model"] != "None" else None,
                    summary["prompt"] if summary["prompt"] != "None" else None,
                    1,
                ),
            )
            c.execute(age_group_insert, (article_id, preference_type, summary["id"], 1))
        else:
            update_statement = f"""
            UPDATE summaries
            SET preference_count = {out["preference_count"] + 1}
            WHERE article_id='{article_id}' AND summary_type = '{preference_type}' AND summary_id = '{summary['id']}';
            """
            c.execute(update_statement)

            c.execute(age_select)
            age_out = c.fetchone()
            if age_out[age_group] is None:
                age_group_update = f"""
                UPDATE age_groups
                SET "{age_group}" = "1"
                WHERE article_id='{article_id}' AND summary_type = '{preference_type}' AND summary_id = '{summary['id']}';
                """
                c.execute(age_group_update)
            else:
                age_val = age_out[age_group]
                age_group_update = f"""
                UPDATE age_groups
                SET "{age_group}" = "{age_val+1}"
                WHERE article_id='{article_id}' AND summary_type = '{preference_type}' AND summary_id = '{summary['id']}';
                """
            c.execute(age_group_update)
