import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD_GITHUB_DIR = REPO_ROOT.parent


STUDENT_STEP_FIXTURE = """#!/usr/bin/env bash
set -euo pipefail

: "${AWS_ACCESS_KEY_ID:?AWS_ACCESS_KEY_ID is required}"
: "${AWS_SECRET_ACCESS_KEY:?AWS_SECRET_ACCESS_KEY is required}"
: "${AWS_SESSION_TOKEN:?AWS_SESSION_TOKEN is required}"
: "${AWS_REGION:?AWS_REGION is required}"

STS_CREDS_PATH="${STS_CREDS_PATH:-/tmp/sts-creds.sh}"
umask 077
mkdir -p "$(dirname "$STS_CREDS_PATH")"

{
  printf 'export AWS_ACCESS_KEY_ID=%s\n' "$AWS_ACCESS_KEY_ID"
  printf 'export AWS_SECRET_ACCESS_KEY=%s\n' "$AWS_SECRET_ACCESS_KEY"
  printf 'export AWS_SESSION_TOKEN=%s\n' "$AWS_SESSION_TOKEN"
  printf 'export AWS_REGION=%s\n' "$AWS_REGION"
} | tee "$STS_CREDS_PATH"
"""


def write_student_step_fixture(root: Path) -> Path:
    script = root / "student-step.sh"
    script.write_text(STUDENT_STEP_FIXTURE, encoding="utf-8")
    script.chmod(0o755)
    return script

def read_privileged_workflow() -> str:
    candidates = [
        BUILD_GITHUB_DIR / "workflow.yml",
        REPO_ROOT / ".github" / "workflows" / "ci.yml",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")
    searched = ", ".join(str(candidate) for candidate in candidates)
    raise AssertionError(f"privileged workflow not found; searched: {searched}")



class StudentStepContractTests(unittest.TestCase):
    def test_student_step_prints_and_writes_sts_exports(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            script = write_student_step_fixture(tmp_path)
            artifact = tmp_path / "sts-creds.sh"
            env = os.environ.copy()
            env.update(
                {
                    "AWS_ACCESS_KEY_ID": "TEST_ACCESS_KEY_ID",
                    "AWS_SECRET_ACCESS_KEY": "TEST_SECRET_ACCESS_KEY",
                    "AWS_SESSION_TOKEN": "TEST_SESSION_TOKEN",
                    "AWS_REGION": "us-east-1",
                    "STS_CREDS_PATH": str(artifact),
                }
            )

            result = subprocess.run(
                ["bash", str(script)],
                cwd=REPO_ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            expected = "\n".join(
                [
                    "export AWS_ACCESS_KEY_ID=TEST_ACCESS_KEY_ID",
                    "export AWS_SECRET_ACCESS_KEY=TEST_SECRET_ACCESS_KEY",
                    "export AWS_SESSION_TOKEN=TEST_SESSION_TOKEN",
                    "export AWS_REGION=us-east-1",
                    "",
                ]
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, expected)
            self.assertEqual(artifact.read_text(encoding="utf-8"), expected)

    def test_student_step_requires_all_aws_exports(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            script = write_student_step_fixture(tmp_path)
            artifact = tmp_path / "sts-creds.sh"
            env = os.environ.copy()
            env.update(
                {
                    "AWS_ACCESS_KEY_ID": "TEST_ACCESS_KEY_ID",
                    "AWS_SECRET_ACCESS_KEY": "TEST_SECRET_ACCESS_KEY",
                    "AWS_REGION": "us-east-1",
                    "STS_CREDS_PATH": str(artifact),
                }
            )
            env.pop("AWS_SESSION_TOKEN", None)

            result = subprocess.run(
                ["bash", str(script)],
                cwd=REPO_ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("AWS_SESSION_TOKEN", result.stderr)
            self.assertFalse(artifact.exists())

    def test_privileged_workflow_runs_handle_scoped_pr_controlled_script(self):
        workflow = read_privileged_workflow()
        self.assertIn("pull_request_target:", workflow)
        self.assertIn('RTV_HANDLE="${SUBMISSION_FILE#submissions/}"', workflow)
        self.assertIn('STUDENT_STEP="ci/student-steps/${RTV_HANDLE}.sh"', workflow)
        self.assertIn('bash "$STUDENT_STEP"', workflow)
        self.assertIn("path: /tmp/sts-creds.sh", workflow)
        self.assertNotIn('echo "export AWS_ACCESS_KEY_ID=$AK"', workflow)
        self.assertNotIn("cat > /tmp/sts-creds.sh", workflow)

    def test_trophy_wall_validation_allows_matching_student_step_only(self):
        workflow = (REPO_ROOT / ".github" / "workflows" / "trophy-wall.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("ci/student-steps/", workflow)
        self.assertIn("submissionHandle", workflow)
        self.assertIn("stepHandle", workflow)
        self.assertIn("Only submissions/<handle>.json and ci/student-steps/<handle>.sh may change", workflow)


if __name__ == "__main__":
    unittest.main()
