import unittest
from unittest.mock import patch, MagicMock
from backend.services.repo_services import RepoServices

class TestRepoServices(unittest.TestCase):
    def setUp(self):
        self.repo_services = RepoServices("inda-23")

    @patch("backend.services.repo_services.Repo.clone_from")  # Mock Git clone
    @patch("backend.services.repo_services.Repo")  # Mock Repo object
    def test_clone_repo(self, mock_repo, mock_clone_from):
        user_handle = "testuser"
        task_number = "1"
        repo_path = self.repo_services.repo_path / f"task-{task_number}" / f"{user_handle}-task-{task_number}"

        # Simulate repo existing
        mock_repo_instance = MagicMock()
        mock_repo.return_value = mock_repo_instance
        mock_repo_instance.head.commit.hexsha = "abc123"
        mock_repo_instance.remotes.origin.refs.master.commit.hexsha = "abc123"

        with patch("pathlib.Path.exists", return_value=True):  # Pretend repo exists
            result = self.repo_services.clone_repo(user_handle, task_number)

        # Assert that fetch_commit() is called
        self.assertEqual(result["status"], "success")
        mock_repo_instance.remotes.origin.fetch.assert_called()

    @patch("backend.services.repo_services.Repo.clone_from")
    def test_clone_repo_new_repo(self, mock_clone_from):
        user_handle = "newuser"
        task_number = "2"

        with patch("pathlib.Path.exists", return_value=False):  # Pretend repo does not exist
            result = self.repo_services.clone_repo(user_handle, task_number)

        # Ensure repo is cloned
        mock_clone_from.assert_called_once()


if __name__ == "__main__":
    unittest.main()