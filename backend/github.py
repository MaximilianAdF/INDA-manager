from dotenv import load_dotenv
from git import Repo
import requests
import json
import os

class StudentRepoManager:
    def __init__(self, org="inda-24", json_path="./data/info/users.json"):
        load_dotenv()

        self.json_path = json_path
        self.data = self.load_json()
        
        # GitHub enterprise configuration
        self.git_url = "https://gits-15.sys.kth.se/api/v3/"
        self.pat_token = os.getenv("GITHUB_PAT")
        self.org = org

        # GitHub API headers
        self.headers = {
            "Authorization": f"Bearer {self.pat_token}",
            "Accept": "application/vnd.github+json"
        }

    def load_json(self):
        """Load student data from JSON."""
        if not os.path.exists(self.json_path):
            raise FileNotFoundError(f"JSON file not found: {self.json_path}")

        with open(self.json_path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError: # Empty JSON file
                return {"students": {}}

    def save_json(self):
        """Save updated data back to JSON."""
        with open(self.json_path, "w") as f:
            json.dump(self.data, f, indent=4)

    def clear_json(self):
        """Clear all student data."""
        self.data = {"students": {}}
        self.save_json()

    def fetch_commit(self, user_handle, task_number):
        """Fetches commit of a repo (clones repo if needed)"""
        repo_path = f"./data/repos/task-{task_number}/{user_handle}-task-{task_number}"

        # Clone repo if it doesn't already exist
        self.clone_repo(repo_path, user_handle, task_number)
        
        # Get last commit info
        try:
            repo = Repo(repo_path)
            last_commit = repo.head.commit
            last_commit_by = last_commit.author.email.removesuffix("@kth.se")
            last_commit_time = last_commit.authored_datetime
            commit_hash = last_commit.hexsha  # Unique commit ID
            self.store_commit(user_handle, str(task_number), last_commit_time, last_commit_by, commit_hash)
        except Exception as e:
            raise Exception(f"Error processing commit for {user_handle} task {task_number}: {e}")


    def clone_repo(self, repo_path, user_handle, task_number):
        """Helper method to clone repo if it doesn't exist."""
        if not os.path.exists(repo_path):
            try:
                repo = Repo.clone_from(
                    f"git@gits-15.sys.kth.se:inda-24/{user_handle}-task-{task_number}.git",
                    repo_path
                )
            except Exception as e:
                raise Exception(f"Error cloning repo for {user_handle} task {task_number}: {e}")



    def store_commit(self, user_handle, task_number, commit_time, commit_by, commit_hash):
        """Stores commit information in JSON."""
        if user_handle != commit_by:
            raise ValueError(f"Commit mismatch: Expected '{user_handle}', but got '{commit_by}'.")

        course = "DD1337" if task_number < 10 else "DD1338"
        
        # Ensure student exists
        self.data.setdefault("students", {})
        self.data["students"].setdefault(user_handle, {})

        # Ensure course exists
        self.data["students"][user_handle].setdefault(course, {})

        # Ensure task exists
        self.data["students"][user_handle][course].setdefault(task_number, {"commit_time": ""})

        # Append new commit
        self.data["students"][user_handle][course][task_number] = {
            "commit_time": commit_time.isoformat(),
            "commit_hash": commit_hash
        }

        # Save JSON after update
        self.save_json()

    def fetch_issue(self, user_handle, task_number):
        """Fetches issue data from GitHub."""
        repo_name = f"{user_handle}-task-{task_number}"
        url = f"{self.git_url}repos/{self.org}/{repo_name}/issues"
        print(url)
        
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()  # Return the list of issues
        elif response.status_code == 404:
            print(response.text)
        elif response.status_code == 403:
            raise Exception(f"❌ Permission issue: {response.text}")
        else:
            raise Exception(f"Failed to fetch issues for {user_handle} task {task_number}: {response.status_code} - {response.text}")


    def get_student_tasks(self, user_handle):
        """Returns all tasks for a given student."""
        if user_handle not in self.data["students"]:
            raise KeyError(f"Student '{user_handle}' not found in records.")
        return self.data["students"][user_handle]


try:
    manager = StudentRepoManager()
    manager.fetch_issue("hugokar", 13)
except Exception as e:
    print(e)