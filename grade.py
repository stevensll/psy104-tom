import csv
import re
from pathlib import Path
import sys

LEGACY_FIELDS = ["question #", "llm response", "correct"]
FIELDS = [
    "question #",
    "llm response",
    "raw correct",
    "osf correct",
    "llm correct",
]
QUESTIONS = Path(__file__).with_name("questions.txt")


def load_answers():
    lines = QUESTIONS.read_text().splitlines()
    answers = {}
    tasks = {}
    for index in range(0, len(lines), 2):
        task, answer = lines[index].split(maxsplit=1)
        number = index // 2 + 1
        answers[number] = answer
        tasks[number] = int(task)
    return answers, tasks


def load_responses(path):
    with path.open(newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames not in (LEGACY_FIELDS, FIELDS):
            raise SystemExit(f"Invalid CSV header in {path}")
        rows = list(reader)

    responses = {}
    for row in rows:
        number = int(row["question #"])
        if number in responses:
            raise SystemExit(f"Duplicate question #{number}")
        responses[number] = {
            "question #": number,
            "llm response": row["llm response"],
            "raw correct": row.get("raw correct", row.get("correct", "")),
            "osf correct": row.get("osf correct", ""),
            "llm correct": row.get("llm correct", ""),
        }
    return responses


def percent(correct, total):
    return f"{correct * 100 / total:g}%"


def source_answer(response):
    words = response.split()
    if not words:
        return ""
    return re.sub(r'''[.,'\"]''', "", words[0])


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python grade.py RESPONSES.csv")

    path = Path(sys.argv[1])
    answers, tasks = load_answers()
    responses = load_responses(path)
    missing = sorted(set(answers) - set(responses))
    extra = sorted(set(responses) - set(answers))
    if missing:
        raise SystemExit(f"Missing {len(missing)} responses")
    if extra:
        raise SystemExit(f"Unknown question #{extra[0]}")

    raw_response_score = 0
    osf_response_score = 0
    raw_task_results = [True] * 40
    osf_task_results = [True] * 40
    rows = []
    for number in sorted(answers):
        row = responses[number]
        raw_correct = (
            row["llm response"].strip().casefold()
            == answers[number].casefold()
        )
        osf_correct = (
            source_answer(row["llm response"]) == answers[number]
        )
        row["raw correct"] = "yes" if raw_correct else "no"
        row["osf correct"] = "yes" if osf_correct else "no"
        raw_response_score += raw_correct
        osf_response_score += osf_correct
        raw_task_results[tasks[number]] &= raw_correct
        osf_task_results[tasks[number]] &= osf_correct
        rows.append(row)

    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)

    raw_task_score = sum(raw_task_results)
    osf_task_score = sum(osf_task_results)
    print(
        "Raw response score: "
        f"{raw_response_score}/640 "
        f"({percent(raw_response_score, 640)})"
    )
    print(
        "Raw task score: "
        f"{raw_task_score}/40 ({percent(raw_task_score, 40)})"
    )
    print(
        "OSF response score: "
        f"{osf_response_score}/640 "
        f"({percent(osf_response_score, 640)})"
    )
    print(
        "OSF task score: "
        f"{osf_task_score}/40 ({percent(osf_task_score, 40)})"
    )

    llm_values = [row["llm correct"] for row in rows]
    if all(value in ("yes", "no") for value in llm_values):
        llm_response_score = sum(value == "yes" for value in llm_values)
        llm_task_results = [True] * 40
        for number, row in zip(sorted(answers), rows):
            llm_task_results[tasks[number]] &= (
                row["llm correct"] == "yes"
            )
        llm_task_score = sum(llm_task_results)
        print(
            "LLM response score: "
            f"{llm_response_score}/640 "
            f"({percent(llm_response_score, 640)})"
        )
        print(
            "LLM task score: "
            f"{llm_task_score}/40 ({percent(llm_task_score, 40)})"
        )


if __name__ == "__main__":
    main()
