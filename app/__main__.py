import json
import secrets
import sqlite3
from random import randint, shuffle

from flask import Flask, redirect, render_template, request, session, url_for

DATABASE = "./database.db"

with open("./Data/NorSumm_dev.json", "r") as f:
    data = json.load(f)

# TODO: Shuffle data for each session
data_skrevet = data[:3]
data_generert = data[:3]  # TODO: Replace with generated data
shuffle(data_generert)

N_ARTICLES = len(data_skrevet)
summary_preferences = {}

app = Flask(__name__)

app.secret_key = secrets.token_hex()


def create_database():
    with sqlite3.connect(DATABASE) as db:
        c = db.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS admins
                    (_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                     password TEXT NOT NULL);"""
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


def update_summary_preferences(article_id, written_id, generated_id, preference_type):
    if article_id not in summary_preferences.keys():
        summary_preferences.update({article_id: {"written": {}, "generated": {}}})

    if written_id not in summary_preferences[article_id]["written"].keys():
        summary_preferences[article_id]["written"].update({written_id: 0})

    if generated_id not in summary_preferences[article_id]["generated"].keys():
        summary_preferences[article_id]["generated"].update({generated_id: 0})

    if preference_type == "written":
        summary_preferences[article_id]["written"][written_id] += 1
    elif preference_type == "generated":
        summary_preferences[article_id]["generated"][generated_id] += 1
    else:
        raise ValueError(f"'{preference_type}', is not a valid preference_type")


def find_article(articles, id):
    for i, dictionary in enumerate(articles):
        if dictionary["id"] == id:
            return i
    raise LookupError(f"The article of id: {id}, was not found.")


def extract_data(idx, article_set_written, article_set_generated: list, form="nb"):
    written = article_set_written[idx]
    generated_idx = find_article(article_set_generated, written["id"])

    summary_written_idx = randint(1, 3)
    summary_generated_idx = randint(1, 3)
    summary_written = article_set_written[idx][f"summaries_{form}"][
        summary_written_idx - 1
    ][f"summary{summary_written_idx}"]
    summary_generated = article_set_generated[generated_idx][f"summaries_{form}"][
        summary_generated_idx - 1
    ][f"summary{summary_generated_idx}"]

    return {
        "id": written["id"],
        "article": written["article"],
        "summary_written_id": f"summary{summary_written_idx}",
        "summary_written": summary_written,
        "summary_generated_id": f"summary{summary_generated_idx}",
        "summary_generated": summary_generated,
    }


@app.route("/", methods=["GET"])
def index():
    return render_template("welcome.html")


@app.route("/start", methods=["POST"])
def start_session():
    print("Starting user session")
    session["current_article"] = 0
    return redirect(url_for("summary_picker"))


@app.route("/summaries", methods=["GET"])
def summary_picker():
    if session["current_article"] == N_ARTICLES:
        return render_template("no_more_summaries.html")

    article = extract_data(session["current_article"], data_skrevet, data_generert)
    summaries = [
        {
            "id": article["summary_written_id"],
            "summary": article["summary_written"],
            "type": "written",
        },
        {
            "id": article["summary_generated_id"],
            "summary": article["summary_generated"],
            "type": "generated",
        },
    ]
    shuffle(summaries)
    return render_template(
        "summary_picker.html",
        article_id=article["id"],
        article=article["article"],
        summary_1=summaries[0],
        summary_2=summaries[1],
    )


@app.route("/select", methods=["POST"])
def select():
    article_id = request.form["article_id"]
    sum1_id, sum1_type = request.form["summary1"].split(" ")
    sum2_id, sum2_type = request.form["summary2"].split(" ")
    preferred = request.form["preferred_type"]
    if sum1_type == preferred:
        if preferred == "written":
            update_summary_preferences(article_id, sum1_id, sum2_id, preferred)
        elif preferred == "generated":
            update_summary_preferences(article_id, sum2_id, sum1_id, preferred)
    elif sum2_type == preferred:
        if preferred == "written":
            update_summary_preferences(article_id, sum2_id, sum1_id, preferred)
        elif preferred == "generated":
            update_summary_preferences(article_id, sum1_id, sum2_id, preferred)
    print(summary_preferences)
    session["current_article"] += 1
    return redirect("/summaries")


@app.route("/terminate", methods=["POST"])
def terminate():
    session["current_article"] = 0
    return redirect(url_for("index"))


@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        with sqlite3.connect(DATABASE) as db:
            db.row_factory = sqlite3.Row
            c = db.cursor()
            c.execute(
                f"""
            SELECT username, password FROM admins
            WHERE username='{username}'
            """
            )
            creds = c.fetchone()

        if not creds:
            return redirect(url_for("admin_login"))
        elif username == creds["username"] and password == creds["password"]:
            session["admin_usr"] = username
            return redirect(url_for("admin_panel"))
        else:
            return redirect(url_for("admin_login"))
    else:
        return render_template("admin_login.html")


@app.route("/admin_panel", methods=["GET"])
def admin_panel():
    if not session.get("admin_usr"):
        return redirect(url_for("admin_login"))
    else:
        return summary_preferences


if __name__ == "__main__":
    create_database()
    app.run(host="0.0.0.0", port=5000, debug=True)
