import requests
import os
from dotenv import load_dotenv
from DirectoryTree import Node, NodeType

load_dotenv()

class GitRepoBrowser:
    def __init__(self, repo_url: str, branch: str = "main", token: str = None):
        """
        Initialize the GitRepoBrowser.

        :param repo_url: URL of the GitHub repository (e.g., https://github.com/user/repo).
        :param branch: Branch to browse (default is 'main').
        :param token: Personal access token for private repositories or higher API limits.
        """
        self.repo_url = repo_url.rstrip("/")
        self.branch = branch
        self.api_url = self._construct_api_url()
        self.headers = {"Authorization": f"token {token}"} if token else {}

    def _construct_api_url(self) -> str:
        """
        Convert the repository URL to the API URL for GitHub.

        :return: API URL for accessing the repository.
        """
        parts = self.repo_url.split("/")
        owner, repo = parts[-2], parts[-1]
        repo = repo.replace(".git", "")  # Remove '.git' from the repository name
        return f"https://api.github.com/repos/{owner}/{repo}"

    def get_directory_tree(self, path: str = "") -> Node:
        """
        Fetch the entire directory tree starting from the specified path.

        :param path: The directory path relative to the repository root.
        :return: A Node object representing the entire directory structure.
        """
        url = f"{self.api_url}/git/trees/{self.branch}?recursive=1"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            tree_data = response.json().get("tree", [])
            root_tree = Node("root", NodeType.DIRECTORY)
            nodes = {"": root_tree}

            for item in tree_data:
                item_path = item["path"]
                parent_path = "/".join(item_path.split("/")[:-1])
                parent_node = nodes.get(parent_path, root_tree)

                if item["type"] == "blob":
                    last_commit_date = self._get_last_commit_date(item_path)
                    if (last_commit_date == "Unknown"):
                        print(f"WARNING: Could not get last commit date for {item_path}")
                        continue
                    new_node = Node(
                        name=item_path.split("/")[-1],
                        type=NodeType.FILE,
                        last_updated=last_commit_date
                    )
                elif item["type"] == "tree":
                    new_node = Node(
                        name=item_path.split("/")[-1],
                        type=NodeType.DIRECTORY
                    )

                parent_node.add_child(new_node)
                nodes[item_path] = new_node

            return root_tree
        else:
            raise RuntimeError(f"Failed to fetch directory tree: {response.status_code} {response.text}")

    def _get_last_commit_date(self, file_path: str) -> str:
        """
        Fetch the last commit date for a given file.

        :param file_path: Path of the file in the repository.
        :return: The last commit date as a string.
        """
        url = f"{self.api_url}/commits?path={file_path}&sha={self.branch}"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            commit_data = response.json()
            if commit_data:
                return commit_data[0]["commit"]["committer"]["date"]
            else:
                return "Unknown"
        else:
            raise RuntimeError(f"Failed to fetch last commit date: {response.status_code} {response.text}")

    def get_file_content(self, file_path: str) -> str:
        """
        Get the content of a file from the repository.

        :param file_path: Path of the file in the repository.
        :return: Content of the file as a string.
        """
        url = f"{self.api_url}/contents/{file_path}?ref={self.branch}"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            file_data = response.json()
            file_content = file_data.get("content", "")
            file_decoded = bytes(file_content, "utf-8").decode("base64")  # Decode base64 content
            return file_decoded
        else:
            raise RuntimeError(f"Failed to get file content: {response.status_code} {response.text}")


# Example Usage:
if __name__ == "__main__":
    # Initialize the GitRepoBrowser with the repository URL and branch
    repo_browser = GitRepoBrowser(
        repo_url="https://github.com/Phiruby/obsidian_notes.git", 
        branch="main", 
        token=os.getenv("GIT_PERSONAL_ACCESS_TOKEN")  # Optional for private repos or higher rate limits
    )

    # Get the directory tree at the root
    try:
        directory_tree = repo_browser.get_directory_tree()
        print("Directory Tree:")
        directory_tree.print_tree()
    except RuntimeError as e:
        print(f"Error: {e}")

