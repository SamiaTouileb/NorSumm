# NorSumm
Norwegian summarization benchmark dataset


### Predictions

The [predictions](./predictions/predictions.tsv) for the development set are in the form of a dataframe, which contains:
* ```model```: name of a generative LM (```LumiOpen/Viking-13B```, ```norallm/normistral-7b-warm```, ```norallm/norbloom-7b-scratch```).
* ```prompt```: the best prompt across six prompts used for evaluation. it is selected by maximizing the BERTScore between the model output and the gold standard.
* ```article```: the input text. differs from the data in this [folder](./Data/) in that the trailing whitespaces around "\n\n" are removed (e.g., " \n\n" becomes "\n\n").
* ```summaries```: the human-written summaries.
* ```predictions```: the model output. generated via grid search. NB: can be empty, so remove this when sampling the data for human evaluation.