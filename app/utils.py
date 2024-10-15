import collections.abc
import json
from copy import copy

import pandas as pd


def parse_predictions(path_to_predictions: str):
    preds = pd.read_csv(path_to_predictions, sep="\t")
    preds = preds.groupby("id", as_index=False).agg(lambda x: list(x))
    parsed_preds = []
    for _, row in preds.iterrows():
        models = row["model"]
        prompts = row["prompt"]
        predictions = row["predictions"]
        out_dict = {
            "id": row["id"],
            "summaries": [
                {f"summary{i+1}": prediction, "model": model, "prompt": prompt}
                for i, (prediction, model, prompt) in enumerate(
                    zip(predictions, models, prompts)
                )
            ],
        }
        parsed_preds.append(out_dict)

    with open("Data/generated_summs.json", "w") as f:
        json.dump(parsed_preds, f)


def _update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = _update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def create_empty_summary(article_id, summary_type, summary_id, model=None, prompt=None):
    summary_dict = {
        article_id: {
            summary_type: {
                summary_id: {
                    "age_groups": {
                        "18-24": 0,
                        "25-34": 0,
                        "35-44": 0,
                        "45-54": 0,
                        "55-64": 0,
                        "65+": 0,
                    },
                    "count": 0,
                    "model": model,
                    "prompt": prompt,
                },
            }
        }
    }
    return summary_dict


def combine_all_summaries(summaries_with_results, written_summs, generated_summs):
    base = summaries_with_results
    with open(written_summs, "r") as f:
        written = json.load(f)
    with open(generated_summs, "r") as f:
        generated = json.load(f)

    out_json = copy(base)

    for article in written:
        if article["id"] in base:
            for summary in article["summaries_nb"]:
                key = list(summary.keys())[0]
                if (
                    "written" in base[article["id"]]
                    and key not in base[article["id"]]["written"]
                ):
                    new_empty = create_empty_summary(
                        article["id"], "written", key, None, None
                    )
                    out_json = _update(out_json, new_empty)
                elif "written" not in base[article["id"]]:
                    new_empty = create_empty_summary(
                        article["id"], "written", key, None, None
                    )
                    out_json = _update(out_json, new_empty)

        else:
            for summary in article["summaries_nb"]:
                key = list(summary.keys())[0]
                new_empty = create_empty_summary(
                    article["id"], "written", key, None, None
                )
                out_json = _update(out_json, new_empty)

    for article in generated:
        if article["id"] in base:
            for summary in article["summaries"]:
                key = list(summary.keys())[0]
                if (
                    "generated" in base[article["id"]]
                    and key not in base[article["id"]]["generated"]
                ):
                    new_empty = create_empty_summary(
                        article["id"],
                        "generated",
                        key,
                        summary["model"],
                        summary["prompt"],
                    )
                    out_json = _update(out_json, new_empty)
                elif "generated" not in base[article["id"]]:
                    new_empty = create_empty_summary(
                        article["id"],
                        "generated",
                        key,
                        summary["model"],
                        summary["prompt"],
                    )
                    out_json = _update(out_json, new_empty)
        else:
            for summary in article["summaries"]:
                key = list(summary.keys())[0]
                new_empty = create_empty_summary(
                    article["id"], "generated", key, summary["model"], summary["prompt"]
                )
                out_json = _update(out_json, new_empty)

    return out_json


if __name__ == "__main__":
    pass
