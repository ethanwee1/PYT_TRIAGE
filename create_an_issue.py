import csv
import argparse
from github import Github
import requests

# Function to get global node ID of an issue using the REST API
def get_issue_global_node_id(issue_url, github_token):
    issue_number = issue_url.split('/')[-1]
    repo_name = '/'.join(issue_url.split('/')[-4:-2])
    url = f"https://api.github.com/repos/{repo_name}/issues/{issue_number}"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()["node_id"]
    else:
        print(f"Failed to get global node ID for issue: {issue_url}")
        return None

# Function to create an issue on GitHub
def create_github_issue(repo, title, body, assignee=None):
    if assignee:
        issue = repo.create_issue(title=title, body=body, assignee=assignee)
    else:
        issue = repo.create_issue(title=title, body=body)
    
    print(f"Issue created: {issue.html_url}")
    return issue

# Function to add an issue to a GitHub project
def add_issue_to_project(issue_global_node_id, project_id, github_token):
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Content-Type": "application/json"
    }
    query = """
    mutation AddToProject($projectId: ID!, $issueId: ID!) {
      addProjectV2ItemById(input: {projectId: $projectId, contentId: $issueId}) {
        item {
          id
        }
      }
    }
    """
    variables = {
        "projectId": project_id,
        "issueId": issue_global_node_id
    }
    response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
    
    if response.status_code == 200:
        print(f"Issue added to project: {response.json()}")
    else:
        print(f"Failed to add issue to project: {response.text}")

# Main function
def main(csv_file, repo_name, token, project_id, assignee=None):
    # Authenticate to GitHub
    g = Github(token)
    repo = g.get_repo(repo_name)

    # Open and read the CSV file
    with open(csv_file, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            # Construct the issue title and body based on the columns in your CSV
            title = f"Test Failed: {row['Failed test']}"
            body = (
                f"### Failed test\n"
                f"- **Failed test**: {row['Failed test']}\n"
                f"- **Arch**: {row['Arch']}\n"
                f"- **Error message**: {row['Error mes']}\n"
                f"- **Track**: {row['Track']}\n"
                f"- **Status**: {row['status']}\n"
            )
            
            # Create the issue
            issue = create_github_issue(repo, title, body, assignee)
            
            # Get the global node ID of the created issue
            issue_global_node_id = get_issue_global_node_id(issue.html_url, token)
            
            if issue_global_node_id:
                # Add the issue to the GitHub project
                add_issue_to_project(issue_global_node_id, project_id, token)

# Argument parser
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create GitHub issues from a CSV file and add them to a project.')
    parser.add_argument('csv_file', help='Path to the CSV file')
    parser.add_argument('repo_name', help='GitHub repository name (e.g., user/repo)')
    parser.add_argument('token', help='GitHub personal access token')
    parser.add_argument('project_id', help='GitHub project ID')
    parser.add_argument('--assignee', help='GitHub username of the assignee for the issues', required=False)
    
    args = parser.parse_args()
    main(args.csv_file, args.repo_name, args.token, args.project_id, args.assignee)
