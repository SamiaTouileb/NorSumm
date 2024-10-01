import json
from random import randint, shuffle

from flask import Flask, redirect, render_template, request

with open("./Data/NorSumm_dev.json", "r") as f:
    data = json.load(f)

shuffle(data)

app = Flask(__name__)


def extract_data(idx, article_set, form="nb"):
    article = article_set[idx]["article"]
    summary_idx = randint(1, 3)
    summary = article_set[idx][f"summaries_{form}"][summary_idx - 1][
        f"summary{summary_idx}"
    ]
    return article, summary


current_article = 0
# art, summ = extract_data(0, data)


@app.route("/", methods=["GET"])
def index():
    return render_template("welcome.html")


@app.route("/summaries", methods=["GET"])
def summary_picker():
    article, summary = extract_data(current_article, data)
    return render_template(
        "summary_picker.html",
        article=article,
        summary_1=summary,
        # summary_2=data[0]["summaries_nb"][1]["summary2"],
        info=data[0]["summaries_nb"][0],
    )


@app.route("/select", methods=["POST"])
def select():
    # print(f"Selected summary: {request.form['selected_summary']}")
    global current_article
    current_article += 1
    return redirect("/summaries")


if __name__ == "__main__":
    # pass
    app.run(host="0.0.0.0", port=5000, debug=True)
