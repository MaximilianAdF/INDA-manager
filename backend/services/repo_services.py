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
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump({"students": {}}, f, indent=4)
            log_debug(f"✅ Created new user data file at {self.json_path}")

        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            if os.stat(self.json_path).st_size == 0:
                log_error(f"❌ Error loading user data: File is empty. (Can be ignored)")
                log_debug(f"✅ Creating new user data structure.")
                return {"students": {}}
            else:
                log_error(f"❌ Error loading user data: {e}")
                return {"students": {}}


    def save_users(self, data: dict) -> None:
        """Function to save user data to JSON file."""
        try:
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            log_info(f"✅ Saved user data to {self.json_path}")
            return {"status": "success"}
        except Exception as e:
            log_error(f"❌ Error saving user data: {e}")
            return {"status": "failed", "reason": str(e)}


    def clone_repo(self, user_handle: str, task_number: str) -> dict:
        """Function to clone/pull a repository for a given user and task number.
        Check if it exists, pull latest changes, fetch latest commit, store commit in JSON."""
        
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
                    f"git@gits-15.sys.kth.se:{self.org_name}/{user_handle}-task-{task_number}.git",
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
        log_info(f"⤵️  Fetching issues for {user_handle}-task-{task_number}")
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            issue_data = {"Pass": None, "Komplettera": None, "Fail": None}

            # Extract relevant issue data, make sure issue was last updated by the TA
            for issue in response.json():
                issue_title = issue["title"]
                issue_user = issue["user"]["login"]
                issue_created_at = issue["created_at"]

                if issue_title not in issue_data:  # Only consider approved issue titles
                    log_debug(f"Skipping issue with title: {issue_title}")
                    continue
                if issue_user != self.ta_handle:  # Only consider issues updated by TA
                    log_debug(f"Skipping issue by non TA: {issue_user}")
                    continue

                if issue_data[issue_title] is None or issue_created_at > issue_data[issue_title]["date"]:
                    issue_data[issue_title] = {
                        "title": issue_title,
                        "body": issue["body"],
                        "state": issue["state"],
                        "date": issue_created_at
                    }

            # Remove None values from issue_data
            issue_data = {k: v for k, v in issue_data.items() if v is not None}

            # Store issue data in JSON
            self.data["students"].setdefault(user_handle, {})
            self.data["students"][user_handle].setdefault(task_number, {})
            self.data["students"][user_handle][task_number]["issues"] = issue_data
            log_info(f"✅ Updated issues for {user_handle}-task-{task_number}")

            self.save_users(self.data)
            return {"status": "success", "message": "Fetched latest issue data.", "data": issue_data}

        else:
            return {"status": "failed", "reason": response.json()["message"]}


    #TODO: Add functionality that keeps track of Komplettering issues and gives the student a
    #week to fix the issue before it is automatically marked as a fail, if the issue is fixed
    #notify the TA that user ... has fixed the issue and the TA can then approve the issue.

    #TODO: Make a countdown timer for the student to fix the issue, if the issue is not fixed.
    #Somehow add it to the body of the issue.
    def create_issue(self, user_handle: str, task_number: str, title: str, body: str) -> dict:
        """Create a new issue on GitHub for a given user and task number."""
        url = f"{self.base_url}repos/{self.org_name}/{user_handle}-task-{task_number}/issues"
        payload = {
            "title": title,
            "body": body,
            "assignees": [user_handle]
        }

        response = requests.post(url, headers=self.headers, json=payload)

        if response.status_code == 201: #Created
            return {"status": "success", "message": "Issue created successfully."}
        else:
            return {"status": "failed", "reason": response.json()["message"]}


#test = RepoServices("inda-24")
#print(test.clone_repo("hugokar", "1"))
#print(test.fetch_issue("hugokar", "1"))
#print(test.create_issue("hugokar", "1", "Test issue", "This is a test issue."))