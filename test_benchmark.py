import contextlib
import csv
import hashlib
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import grade
import run

ROOT = Path(__file__).parent
CORPUS_HASH = (
    "2a25a20e651190c35f9c40789f0dee75"
    "af56094d0928c23f5f85dc7b8d842135"
)


def load_corpus():
    lines = (ROOT / "questions.txt").read_text().splitlines()
    records = []
    for index in range(0, len(lines), 2):
        task, answer = lines[index].split(maxsplit=1)
        records.append((int(task), answer, lines[index + 1]))
    return records


class BenchmarkTest(unittest.TestCase):
    def test_corpus_shape_and_hash(self):
        contents = (ROOT / "questions.txt").read_bytes()
        records = load_corpus()
        task_counts = {
            task: sum(record[0] == task for record in records)
            for task in range(40)
        }

        self.assertEqual(hashlib.sha256(contents).hexdigest(), CORPUS_HASH)
        self.assertEqual(len(records), 640)
        self.assertEqual(set(task_counts.values()), {16})
        self.assertEqual(len({record[2] for record in records}), 640)

    def test_runner_uses_fresh_isolated_session_and_effort(self):
        result = SimpleNamespace(returncode=0, stdout="beer\n", stderr="")
        with mock.patch.object(
            run.subprocess,
            "run",
            return_value=result,
        ) as call:
            self.assertEqual(
                run.ask("provider/model", "high", (1, "prompt")),
                (1, "beer"),
            )

        arguments = call.call_args.args[0]
        self.assertIn("--no-session", arguments)
        self.assertIn("--no-tools", arguments)
        self.assertIn("--no-rules", arguments)
        self.assertEqual(
            arguments[arguments.index("--thinking") + 1],
            "high",
        )
        self.assertEqual(
            arguments[arguments.index("--system-prompt") + 1],
            run.SYSTEM,
        )

    def test_grader_is_stricter_than_source_scorer(self):
        self.assertEqual(grade.source_answer("dryer."), "dryer")
        self.assertEqual(
            grade.source_answer("Internal Affairs"),
            "Internal",
        )
        self.assertNotEqual("dryer.".strip().casefold(), "dryer")
        self.assertNotEqual(
            "Internal Affairs".strip().casefold(),
            "internal",
        )

    def test_three_pass_grading_and_strict_tasks(self):
        records = load_corpus()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "responses.csv"
            with path.open("w", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=grade.FIELDS)
                writer.writeheader()
                for number, (_, answer, _) in enumerate(records, 1):
                    response = answer + "." if number == 1 else answer
                    writer.writerow(
                        {
                            "question #": number,
                            "llm response": response,
                            "raw correct": "",
                            "osf correct": "",
                            "llm correct": "yes",
                        }
                    )

            output = io.StringIO()
            with mock.patch.object(
                grade.sys,
                "argv",
                ["grade.py", str(path)],
            ):
                with contextlib.redirect_stdout(output):
                    grade.main()

            self.assertEqual(
                output.getvalue(),
                "Raw response score: 639/640 (99.8438%)\n"
                "Raw task score: 39/40 (97.5%)\n"
                "OSF response score: 640/640 (100%)\n"
                "OSF task score: 40/40 (100%)\n"
                "LLM response score: 640/640 (100%)\n"
                "LLM task score: 40/40 (100%)\n",
            )
            with path.open(newline="") as file:
                rows = list(csv.DictReader(file))
            self.assertEqual(rows[0]["raw correct"], "no")
            self.assertEqual(rows[0]["osf correct"], "yes")
            self.assertEqual(rows[0]["llm correct"], "yes")
            self.assertTrue(
                all(row["raw correct"] == "yes" for row in rows[1:])
            )


if __name__ == "__main__":
    unittest.main()
