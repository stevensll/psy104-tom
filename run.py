from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from pathlib import Path
import subprocess
import sys

FIELDS = [
    "question #",
    "llm response",
    "raw correct",
    "osf correct",
    "llm correct",
]
QUESTIONS = Path(__file__).with_name("questions.txt")
SYSTEM = "Complete the text with exactly one word. No explanations."


def load_questions():
    lines = QUESTIONS.read_text().splitlines()
    return [
        (index // 2 + 1, lines[index + 1])
        for index in range(0, len(lines), 2)
    ]


def load_completed(path):
    if not path.exists() or path.stat().st_size == 0:
        return set()
    with path.open(newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != FIELDS:
            raise SystemExit(f"Invalid CSV header in {path}")
        return {int(row["question #"]) for row in reader}


def ask(model, effort, question):
    number, prompt = question
    arguments = [
        "omp",
        "-p",
        "--no-session",
        "--no-tools",
        "--no-rules",
        "--no-skills",
        "--no-extensions",
        "--model",
        model,
    ]
    if effort:
        arguments.extend(["--thinking", effort])
    arguments.extend(["--system-prompt", SYSTEM, prompt])
    result = subprocess.run(
        arguments,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        return number, None
    return number, result.stdout.strip()


def main():
    if len(sys.argv) not in (3, 4):
        raise SystemExit(
            "Usage: python run.py MODEL RESPONSES.csv [EFFORT]"
        )

    model = sys.argv[1]
    path = Path(sys.argv[2])
    effort = sys.argv[3] if len(sys.argv) == 4 else None
    completed = load_completed(path)
    pending = [q for q in load_questions() if q[0] not in completed]
    write_header = not path.exists() or path.stat().st_size == 0
    failures = 0

    with path.open("a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        if write_header:
            writer.writeheader()
        with ThreadPoolExecutor(max_workers=40) as pool:
            futures = [
                pool.submit(ask, model, effort, q)
                for q in pending
            ]
            for future in as_completed(futures):
                number, response = future.result()
                if response is None:
                    failures += 1
                    continue
                writer.writerow(
                    {
                        "question #": number,
                        "llm response": response,
                        "raw correct": "",
                        "osf correct": "",
                        "llm correct": "",
                    }
                )
                file.flush()

    if failures:
        raise SystemExit(
            f"{failures} calls failed; rerun the same command to retry"
        )
    print(f"Collected {len(completed) + len(pending)}/640 responses")


if __name__ == "__main__":
    main()
