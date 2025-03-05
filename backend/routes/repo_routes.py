from flask import Blueprint, jsonify
from backend.utils.logger import log_info
from backend.services.repo_services import clone_repo

repo_bp = Blueprint('repo_routes', __name__)

@repo_bp.route("/clone-repos", methods=["POST"])
def clone_repos():
    """Clone all user repositories for a given task"""
    data = request.get_json()
    log_info(f"Received request to clone repositories for task: {data['task_id']}")

    status = {user: clone_repo(user, data["task_id"]) for user in data["users"]}
    response = {user: "success" if res["status"] == "success" else "failed" for user, res in status.items()}
    response["reasons"] = {user: res["reason"] for user, res in status.items() if res["status"] != "success"}

    return jsonify(response)



@repo_bp.route("/update-repos", methods=["POST"])
def update_repo():
    """Clone a given user's repository for a given task"""
    data = request.get_json()
    log_info(f"Received request to pull repository changes for {data['user']} task: {data['task_id']}")
    
    response = clone_repo(data["user"], data["task_id"])
    return jsonify(response)




