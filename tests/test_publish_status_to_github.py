import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLISHER = ROOT / "scripts/publish_status_to_github.sh"


class PublishStatusToGitHubTests(unittest.TestCase):
    def test_stages_tracked_host_amr_decision_deletion_by_exact_path(self):
        text = PUBLISHER.read_text(encoding="utf-8")

        self.assertIn(
            'HOST_AMR_DECISION_REQUEST="decision_requests/metagenome_host_amr_requirements.md"',
            text,
        )
        self.assertIn(
            'git ls-files --error-unmatch -- "$HOST_AMR_DECISION_REQUEST"',
            text,
        )
        self.assertIn('git add -- "$HOST_AMR_DECISION_REQUEST"', text)
        self.assertNotIn("git add -u", text)
        self.assertNotIn("git add -A", text)


if __name__ == "__main__":
    unittest.main()
