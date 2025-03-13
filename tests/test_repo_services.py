import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import os
from backend.services.repo_services import RepoServices

class TestRepoServices(unittest.TestCase):
    def setUp(self):
        """Set up test instance and mock .env variables"""
        os.environ["GITHUB_PAT"] = "fake_token"
        os.environ["TA_HANDLE"] = "fake_ta"
        self.repo_service = RepoServices("inda-24")

    @patch("builtins.open", new_callable=mock_open, read_data='{"students": {}}')
    @patch("backend.utils.logger.log_debug")
    def test_load_users_existing_file(self, mock_log, mock_open_file):
        """Test loading users when JSON file exists"""
        data = self.repo_service.load_users()
        self.assertEqual(data, {"students": {}})
        mock_log.assert_called_with(f"✅ Created new user data file at {self.repo_service.json_path}")

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.stat")
    @patch("backend.utils.logger.log_error")
    def test_load_users_empty_file(self, mock_log, mock_stat, mock_open_file):
        """Test loading users when file is empty"""
        mock_stat.return_value.st_size = 0
        data = self.repo_service.load_users()
        self.assertEqual(data, {"students": {}})
        mock_log.assert_called_with("❌ Error loading user data: File is empty. (Can be ignored)")

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    @patch("backend.utils.logger.log_info")
    def test_save_users(self, mock_log, mock_json_dump, mock_open_file):
        """Test saving user data"""
        data = {"students": {"test_user": {}}}
        result = self.repo_service.save_users(data)
        self.assertEqual(result, {"status": "success"})
        mock_json_dump.assert_called_once()
        mock_log.assert_called_with(f"✅ Saved user data to {self.repo_service.json_path}")

    @patch("backend.services.repo_services.Repo.clone_from")
    @patch("backend.utils.logger.log_info")
    def test_clone_repo_success(self, mock_log, mock_clone):
        """Test cloning a repository"""
        result = self.repo_service.clone_repo("test_user", "1")
        mock_clone.assert_called_once()
        mock_log.assert_called_with("✅ Cloned repo for test_user-task-1")
        self.assertEqual(result["status"], "success")

    @patch("backend.services.repo_services.requests.get")
    def test_fetch_issue_success(self, mock_requests):
        """Test fetching issues with a mocked API response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"title": "Pass", "user": {"login": "fake_ta"}, "created_at": "2024-02-26T12:00:00Z", "body": "Good job!"}
        ]
        mock_requests.return_value = mock_response

        result = self.repo_service.fetch_issue("test_user", "1")
        self.assertEqual(result["status"], "success")
        self.assertIn("Pass", result["data"])

    @patch("backend.services.repo_services.requests.post")
    def test_create_issue_success(self, mock_requests):
        """Test issue creation with mocked API response"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_requests.return_value = mock_response

        result = self.repo_service.create_issue("test_user", "1", "Test Issue", "This is a test issue.")
        self.assertEqual(result["status"], "success")

if __name__ == "__main__":
    unittest.main()
    