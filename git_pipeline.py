import json
from git_services.GitService import GitRepoBrowser
import os 

def load_json_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

if __name__ == "__main__":
    file_path = "config/latest_tree.json"
    data = load_json_from_file(file_path)
    fresh_run = False
    if ("tree" not in data.keys() or "last_updated" not in data.keys()):
        # not previous runs, make a new run
        fresh_run = True
    # load the git tree data
    repo_browser = GitRepoBrowser(
        repo_url="https://github.com/Phiruby/obsidian_notes.git", 
        branch="main", 
        token=os.getenv("GIT_PERSONAL_ACCESS_TOKEN")  # Optional for private repos or higher rate limits
    )
    directory_tree = repo_browser.get_directory_tree()
    