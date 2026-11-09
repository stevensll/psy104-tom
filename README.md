# TOM experiment

This is a replication of the theory of mind task conducted in the Kosinki study.
The questions were retrieved from their public github repo: 
https://osf.io/csdhb/wiki?wiki=c4qv7


This project tests language models with 40 false-belief tasks. Each task has
16 variations. This gives 640 questions for each model.

A task passes only when the model answers all 16 variations correctly.

## Results

Each table entry shows `correct responses / tasks passed`.

| Model | Raw match | OSF method | AI review |
|---|---:|---:|---:|
| Codex Luna low | 504/640 · 10/40 | 534/640 · 10/40 | 565/640 · 13/40 |
| Codex Luna medium | 504/640 · 12/40 | 519/640 · 12/40 | 558/640 · 16/40 |
| Codex Luna high | 509/640 · 13/40 | 523/640 · 15/40 | 571/640 · 18/40 |
| Codex Luna max | 530/640 · 16/40 | 543/640 · 23/40 | 590/640 · 26/40 |
| Codex Luna xhigh | 517/640 · 15/40 | 530/640 · 16/40 | 571/640 · 19/40 |
| Codex Sol low | 557/640 · 22/40 | 565/640 · 26/40 | 601/640 · 29/40 |
| Codex Sol medium | 545/640 · 18/40 | 569/640 · 28/40 | **606/640 · 32/40** |
| Codex Sol high | 555/640 · 23/40 | 565/640 · 28/40 | **605/640 · 32/40** |
| Codex Terra low | 544/640 · 12/40 | 560/640 · 12/40 | 586/640 · 16/40 |
| Gemini 2.5 Flash | 566/640 · 25/40 | 566/640 · 25/40 | 599/640 · 30/40 |

- **Raw match:** The response must match the expected word exactly.
- **OSF method:** This follows the scoring method from the original study.
- **AI review:** An AI (codex 5.6 medium) checks whether the response has the correct meaning.

Codex Sol medium had the highest AI-reviewed response score. Codex Sol medium
and Codex Sol high tied for the highest task score.

## Files

- `questions.txt` contains the 640 questions and expected answers.
- `run.py` asks a model every question and saves its responses in a CSV file.
  It sends up to 40 questions at the same time. If a run stops, use the same
  command again to continue it.
- `grade.py` grades a response file and prints the three scores.
- The CSV files contain each model's responses and its saved grades.
- `test_benchmark.py` checks that the questions and scoring still work as
  intended. Most users do not need to run this file.

## Usage

OMP must already be installed and connected to the model provider. This allows
easy subagent splitting.

To view the scores for an existing result file:

```bash
python grade.py codex-sol-medium.csv
```

To test another model:

```bash
python run.py MODEL_NAME my-results.csv
python grade.py my-results.csv
```

You can also give a model an effort level:

```bash
python run.py openai-codex/gpt-5.6-sol my-results.csv medium
```

The first command collects the 640 responses. The grading command fills in
and reports the raw and OSF scores. A new file needs a separate AI review
before it has an AI-reviewed score. The result files already included in this
project have all three grades.
