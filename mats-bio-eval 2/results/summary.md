# Results summary

Model rows are the mean of the per-epoch scores in the prediction CSVs.

## Baselines

| Set | Predictor | Accuracy | Balanced accuracy | MCC |
| --- | --- | --- | --- | --- |
| robust 98 | hydrophobicity | 0.684 | 0.686 | 0.380 |
| robust 98 | random_seed0 | 0.531 | 0.532 | 0.064 |
| robust 98 | always_away | 0.490 | 0.500 | 0.000 |
| all 107 | hydrophobicity | 0.682 | 0.681 | 0.370 |
| all 107 | random_seed0 | 0.523 | 0.523 | 0.046 |
| all 107 | always_away | 0.505 | 0.500 | 0.000 |

## Truth alternation

Within-strand ±1 autocorrelation of the chromophore labels: lag 1 -0.856, lag 2 0.788, adjacent-flip fraction 0.927.

## Models

| Model | max_tokens | Epochs | Robust accuracy | All accuracy | Balanced accuracy | MCC | Unparsed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| together/meta-llama/Llama-3.3-70B-Instruct-Turbo | task default | 1 | 0.480 | 0.495 | 0.491 | -0.055 | 0.000 |
| together/openai/gpt-oss-120b | 2048 | 1 | 0.694 | 0.692 | 0.692 | 0.383 | 0.000 |
| together/openai/gpt-oss-120b | task default | 1 | 0.071 | 0.065 | 0.066 | -0.873 | 0.897 |

## Task 2: gfp_tolerant_site

| Model | max_tokens | n | Strict | Start only | Expected by chance |
| --- | --- | --- | --- | --- | --- |
| together/meta-llama/Llama-3.3-70B-Instruct-Turbo | task default | 5 | 0/5 | 3/5 | 2.19/5 |
| together/openai/gpt-oss-120b | 2048 | 5 | 2/5 | 2/5 | 2.19/5 |

`together/meta-llama/Llama-3.3-70B-Instruct-Turbo` named an accepted start but quoted a triple that does not match the reference there in 3 bracket(s): 1-50, 101-150, 151-200. Those count as incorrect under the task scorer.
