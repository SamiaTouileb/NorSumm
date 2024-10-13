import json
import secrets
from random import randint, shuffle, sample

from db_funcs import create_database, fetch_summaries_json, get_credentials, summary_db
from flask import Flask, redirect, render_template, request, session, url_for

DATABASE = "./database.db"

with open("./Data/NorSumm_dev.json", "r") as f:
    DATA_WRITTEN = json.load(f)

with open("./Data/generated_summs.json", "r") as f:
    DATA_GENERATED = json.load(f)

DATA_WRITTEN = DATA_WRITTEN[:]
DATA_GENERATED = DATA_GENERATED[:]

N_ARTICLES = len(DATA_WRITTEN)

app = Flask(__name__)

app.secret_key = secrets.token_hex()


def find_article(articles, id):
    for i, dictionary in enumerate(articles):
        if dictionary["id"] == id:
            return i
    raise LookupError(f"The article of id: {id}, was not found.")


def extract_data(idx, article_set_written, article_set_generated: list, form="nb"):
    written = article_set_written[idx]
    generated_idx = find_article(article_set_generated, written["id"])

    summary_written_idx = randint(1, 3)
    summary_written = article_set_written[idx][f"summaries_{form}"][
        summary_written_idx - 1
    ][f"summary{summary_written_idx}"]

    g_summaries = list(enumerate(article_set_generated[generated_idx]["summaries"]))
    shuffle(g_summaries)
    summary_generated_index = next(
        i for i, summary in g_summaries if summary[f"summary{i+1}"] is not None
    )

    summary_generated = article_set_generated[generated_idx]["summaries"][
        summary_generated_index
    ][f"summary{summary_generated_index+1}"]
    model_generated = article_set_generated[generated_idx]["summaries"][
        summary_generated_index
    ]["model"]
    prompt_generated = article_set_generated[generated_idx]["summaries"][
        summary_generated_index
    ]["prompt"]

    return {
        "id": written["id"],
        "article": written["article"],
        "summary_written_id": f"summary{summary_written_idx}",
        "summary_written": summary_written,
        "summary_generated_id": f"summary{summary_generated_index+1}",
        "summary_generated": summary_generated,
        "summary_generated_model": model_generated,
        "summary_generated_prompt": prompt_generated,
    }


@app.route("/", methods=["GET"])
def index():
    return render_template("welcome.html")


@app.route("/start", methods=["POST"])
def start_session():
    session["article_order"] = sample(range(len(DATA_WRITTEN)), len(DATA_WRITTEN))
    session["current_article"] = 0
    return redirect(url_for("select_age"))


@app.route("/age", methods=["GET", "POST"])
def select_age():
    if request.method == "GET":
        return render_template("select_age.html")
    else:
        age_group = request.form["age_group"]
        session["age_group"] = age_group
        return redirect(url_for("summary_picker"))


@app.route("/summaries", methods=["GET"])
def summary_picker():
    if session["current_article"] == N_ARTICLES:
        return render_template("no_more_summaries.html")

    article_idx = session["article_order"][session["current_article"]]
    article = extract_data(article_idx, DATA_WRITTEN, DATA_GENERATED)
    summaries = [
        {
            "id": article["summary_written_id"],
            "summary": article["summary_written"],
            "type": "written",
            "model": None,
            "prompt": None,
        },
        {
            "id": article["summary_generated_id"],
            "summary": article["summary_generated"],
            "type": "generated",
            "model": article["summary_generated_model"],
            "prompt": article["summary_generated_prompt"],
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

    keys = ["id", "type", "model", "prompt"]
    sum1 = {k: v for (k, v) in zip(keys, request.form["summary1"].split("<split>"))}
    sum2 = {k: v for (k, v) in zip(keys, request.form["summary2"].split("<split>"))}
    preferred = request.form["preferred_type"]
    if sum1["type"] == preferred:
        summary_db(DATABASE, article_id, preferred, sum1, session["age_group"])
    elif sum2["type"] == preferred:
        summary_db(DATABASE, article_id, preferred, sum2, session["age_group"])
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

        creds = get_credentials(DATABASE, username)

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
        return fetch_summaries_json(DATABASE)


if __name__ == "__main__":
    create_database(DATABASE)
    app.run(host="0.0.0.0", port=5000, debug=True)
