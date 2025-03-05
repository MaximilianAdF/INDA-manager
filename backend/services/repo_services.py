from backend.utils.logger import log_info, log_error, log_debug
from dotenv import load_dotenv
from pathlib import Path
from git import Repo
import requests
import json
import os


# Load env variables from .env file
load_dotenv()

class RepoServices:
    def __init__(self, org_name):
        """
        Initialize RepoServices with organization name.
        Loads API token & TA handle from environment variables.
        """
        self.org_name = org_name
        self.ta_handle = os.getenv("TA_HANDLE")
        self.api_token = os.getenv("GITHUB_PAT") #TODO: Make a function that fetches from .env file and raises error if not found
        self.base_url = "https://gits-15.sys.kth.se/api/v3/"
        self.repo_path = Path(__file__).resolve().parent.parent.parent / "data" / "repos"
        self.json_path = Path(__file__).resolve().parent.parent.parent / "data" / "info" / "students.json"
        
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Accept": "application/vnd.github+json"
        }
    
        self.data = self.load_users()


    def load_users(self) -> dict:
        """Function to load user data from JSON file."""
        if not self.json_path.exists():
            self.json_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.json_path, "w") as f:
                json.dump({"students": {}}, f, indent=4)
            log_debug(f"Created new user data file at {self.json_path}")

        try:
            with open(self.json_path, "r") as f:
                return json.load(f)
        except Exception as e:
            log_error(f"❌ Error loading user data: {e}")
            return {"students": {}}


    def save_users(self, data: dict) -> None:
        """Function to save user data to JSON file."""
        try:
            with open(self.json_path, "w") as f:
                json.dump(data, f, indent=4)
            log_info(f"✅ Saved user data to {self.json_path}")
            return {"status": "success"}
        except Exception as e:
            log_error(f"❌ Error saving user data: {e}")
            return {"status": "failed", "reason": str(e)}


    # TODO: Implement functionality for recloning repo when it already exists
    # Maybe update json structure to store one commit for first hand in
    # and another for the eventual "Komplettering" hand in
    def clone_repo(self, user_handle: str, task_number: str) -> dict:
        """Function to clone/pull a repository for a given user and task number."""
        repo_dir = self.repo_path / f"task-{task_number}" / f"{user_handle}-task-{task_number}"

        try: 
            if repo_dir.exists(): # Repo exists, pull changes instead
                repo = Repo(repo_dir)
                origin = repo.remotes.origin
                origin.fetch()

                # Get latest commit hash from remote
                remote_commit_hash = origin.refs.master.commit.hexsha
                local_commit_hash = repo.head.commit.hexsha

                if remote_commit_hash == local_commit_hash:
                    log_info(f"✅ No updates for {user_handle}-task-{task_number}, latest commit hash is the same.")
                    return {"status": "success", "message": "No updates, latest commit hash is the same."}
                else:
                    origin.pull()
                    log_info(f"✅ Pulled repo for {user_handle}-task-{task_number}")

            else:
                Repo.clone_from(
                    f"git@gits-15.sys.kth.se:inda-24/{user_handle}-task-{task_number}.git",
                    f"{self.repo_path}/task-{task_number}/{user_handle}-task-{task_number}"
                )
                log_info(f"✅ Cloned repo for {user_handle}-task-{task_number}")
            
            return self.fetch_commit(user_handle, task_number)
            
        except Exception as e:
            log_error(f"❌ Error handling repo for {user_handle}-task-{task_number}: {e}")
            return {"status": "failed", "reason": str(e)}


    def fetch_commit(self, user_handle: str, task_number: str) -> dict:
        """Function to fetch & store last commit for a given user and task number."""
        try:
            repo = Repo(self.repo_path / f"task-{task_number}" / f"{user_handle}-task-{task_number}")

            last_commit = repo.head.commit
            commit_author = last_commit.author.email.removesuffix("@kth.se")
            commit_timestamp = last_commit.authored_datetime
            commit_hash = last_commit.hexsha

            return self.store_commit(user_handle, task_number, commit_timestamp, commit_author, commit_hash) # Helper function 

        except Exception as e:
            return {"status": "failed", "reason": str(e)}


    def store_commit(self, user_handle: str, task_number: str, commit_timestamp, commit_author: str, commit_hash: str) -> dict:
        """Helper function to store commit in JSON file."""
        try:
            self.data["students"].setdefault(user_handle, {})
            self.data["students"][user_handle].setdefault(task_number, {})
            store_as = "clone" if "clone" not in self.data["students"][user_handle][task_number] else "pull"

            # If first pull already stored, update last pull (Komplettering)
            self.data["students"][user_handle][task_number][store_as] = {
                "commit_timestamp": commit_timestamp.isoformat(),
                "commit_author": commit_author,
                "commit_hash": commit_hash
            }

            log_info(f"✅ Stored {store_as} commit for {user_handle}-task-{task_number}")
            return self.save_users(self.data)
 
        except Exception as e:
            return {"status": "failed", "reason": str(e)}


    def fetch_issue(self, user_handle: str, task_number: str) -> dict:
        """Fetches issue data from GitHub."""
        url = f"{self.base_url}repos/{self.org_name}/{user_handle}-task-{task_number}/issues"

        log_info(f"⤵️ Fetching issues for {user_handle}-task-{task_number}")
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            # Extact relevant issue data, make sure issue was last updated by the TA
            for issue in response.json():
                if issue["title"] not in ["Pass", "Komplettera", "Fail"]: # Only consider approved issue titles
                    log_debug(f"Skipping issue with title: {issue['title']}")
                    continue
                if issue["user"]["login"] != self.ta_handle: # Only consider issues updated by TA
                    log_debug(f"Skipping issue by non TA: {issue['user']['login']}")
                    continue

                issue_data = {
                    "title": issue["title"],
                    "body": issue["body"],
                    "date": issue["created_at"]
                }

                # Store issue data in JSON


            
        else:
            return {"status": "failed", "reason": response.json()["message"]}

test = RepoServices("inda-24")
print(test.clone_repo("hugokar", "1"))
print(test.fetch_issue("hugokar", "1"))