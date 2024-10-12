import json

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


if __name__ == "__main__":
    parse_predictions("predictions/predictions.tsv")
