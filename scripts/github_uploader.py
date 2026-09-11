"""
MoodswingsFan - Direct GitHub API Repository Creator & Code Pusher
Creates https://github.com/<owner>/moodswingsfan and pushes all codebase files
using GitHub REST & Git Database API without requiring local git.exe.
"""

import os
import sys
import base64
import requests

GITHUB_API = "https://api.github.com"
DEFAULT_REPO_NAME = "moodswingsfan"
DEFAULT_OWNER = "navaneethkrishnar227"

IGNORE_DIRS = {
    "venv", ".venv", "env", "__pycache__", ".git", ".idea", ".vscode", "scratch", ".system_generated"
}
IGNORE_FILES = {
    ".DS_Store", "thumbs.db"
}


def get_headers(token: str):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "MoodswingsFan-Uploader",
    }


def create_or_get_repo(token: str, repo_name: str = DEFAULT_REPO_NAME, private: bool = False):
    headers = get_headers(token)
    user_res = requests.get(f"{GITHUB_API}/user", headers=headers)
    if user_res.status_code != 200:
        raise RuntimeError(f"Authentication failed ({user_res.status_code}): {user_res.json().get('message')}")
    
    username = user_res.json().get("login")
    print(f"[+] Authenticated as GitHub user: @{username}")

    # Check if repo exists
    repo_res = requests.get(f"{GITHUB_API}/repos/{username}/{repo_name}", headers=headers)
    if repo_res.status_code == 200:
        print(f"[i] Repository https://github.com/{username}/{repo_name} already exists.")
        return username, repo_res.json()

    # Create repo
    payload = {
        "name": repo_name,
        "description": "MoodswingsFan - Real-Time Facial Emotion Detection & Smart Climate AI",
        "private": private,
        "auto_init": True,  # Creates initial commit with README so main branch exists
    }
    create_res = requests.post(f"{GITHUB_API}/user/repos", headers=headers, json=payload)
    if create_res.status_code not in (200, 201):
        raise RuntimeError(f"Failed to create repository: {create_res.json().get('message')}")
    
    print(f"[+] Successfully created repository: https://github.com/{username}/{repo_name}")
    return username, create_res.json()


def collect_files(root_dir: str):
    files_to_push = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith(".")]
        for fname in filenames:
            if fname in IGNORE_FILES or fname.endswith(".pyc") or fname.endswith(".tmp"):
                continue
            full_path = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(full_path, root_dir).replace("\\", "/")
            files_to_push.append((rel_path, full_path))
    return files_to_push


def push_files(token: str, username: str, repo_name: str, root_dir: str):
    headers = get_headers(token)
    files = collect_files(root_dir)
    print(f"[+] Found {len(files)} project files to upload.")

    # Get latest commit on main branch
    ref_res = requests.get(f"{GITHUB_API}/repos/{username}/{repo_name}/git/refs/heads/main", headers=headers)
    if ref_res.status_code == 404:
        # Retry with 'master' if needed
        ref_res = requests.get(f"{GITHUB_API}/repos/{username}/{repo_name}/git/refs/heads/master", headers=headers)
        branch = "master"
    else:
        branch = "main"

    base_tree_sha = None
    parent_commit_sha = None
    if ref_res.status_code == 200:
        parent_commit_sha = ref_res.json()["object"]["sha"]
        commit_res = requests.get(f"{GITHUB_API}/repos/{username}/{repo_name}/git/commits/{parent_commit_sha}", headers=headers)
        if commit_res.status_code == 200:
            base_tree_sha = commit_res.json()["tree"]["sha"]

    # Upload blobs
    tree_items = []
    for i, (rel_path, full_path) in enumerate(files, 1):
        print(f"  ({i}/{len(files)}) Staging blob: {rel_path}...")
        with open(full_path, "rb") as f:
            content = f.read()
        
        blob_payload = {
            "content": base64.b64encode(content).decode("utf-8"),
            "encoding": "base64"
        }
        blob_res = requests.post(f"{GITHUB_API}/repos/{username}/{repo_name}/git/blobs", headers=headers, json=blob_payload)
        if blob_res.status_code not in (200, 201):
            raise RuntimeError(f"Failed to upload blob {rel_path}: {blob_res.text}")
        
        blob_sha = blob_res.json()["sha"]
        tree_items.append({
            "path": rel_path,
            "mode": "100644",
            "type": "blob",
            "sha": blob_sha
        })

    # Create Tree
    tree_payload = {"tree": tree_items}
    if base_tree_sha:
        tree_payload["base_tree"] = base_tree_sha

    tree_res = requests.post(f"{GITHUB_API}/repos/{username}/{repo_name}/git/trees", headers=headers, json=tree_payload)
    if tree_res.status_code not in (200, 201):
        raise RuntimeError(f"Failed to create tree: {tree_res.text}")
    new_tree_sha = tree_res.json()["sha"]

    # Create Commit
    commit_payload = {
        "message": "Initial commit: MoodswingsFan facial emotion AI & smart climate controller with full README",
        "tree": new_tree_sha,
        "parents": [parent_commit_sha] if parent_commit_sha else []
    }
    commit_res = requests.post(f"{GITHUB_API}/repos/{username}/{repo_name}/git/commits", headers=headers, json=commit_payload)
    if commit_res.status_code not in (200, 201):
        raise RuntimeError(f"Failed to create commit: {commit_res.text}")
    new_commit_sha = commit_res.json()["sha"]

    # Update or Create Ref
    ref_payload = {"sha": new_commit_sha, "force": True}
    if parent_commit_sha:
        update_res = requests.patch(f"{GITHUB_API}/repos/{username}/{repo_name}/git/refs/heads/{branch}", headers=headers, json=ref_payload)
    else:
        ref_payload["ref"] = f"refs/heads/{branch}"
        update_res = requests.post(f"{GITHUB_API}/repos/{username}/{repo_name}/git/refs", headers=headers, json=ref_payload)

    if update_res.status_code not in (200, 201):
        raise RuntimeError(f"Failed to update ref: {update_res.text}")

    print("\n" + "=" * 60)
    print(f"[SUCCESS] Code successfully pushed to:")
    print(f"  https://github.com/{username}/{repo_name}")
    print("=" * 60)


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if len(sys.argv) > 1:
        token = sys.argv[1]
    
    if not token:
        print("[!] Error: No GitHub Personal Access Token provided.")
        print("Usage: python scripts/github_uploader.py <YOUR_GITHUB_PERSONAL_ACCESS_TOKEN>")
        print("Or set GITHUB_TOKEN environment variable.")
        sys.exit(1)

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    username, _ = create_or_get_repo(token, DEFAULT_REPO_NAME)
    push_files(token, username, DEFAULT_REPO_NAME, project_root)


if __name__ == "__main__":
    main()
