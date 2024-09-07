import csv
import argparse
from github import Github
import requests

# Function to create an issue on GitHub
def create_github_issue(repo, title, body, assignee=None):
    issue = repo.create_issue(title=title, body=body, assignee=assignee)
    print(f"Issue created: {issue.html_url}")
    return issue

# Function to add an issue to a GitHub project
def add_issue_to_project(issue_url, project_id, github_token):
    # Extract issue number from URL
    issue_number = issue_url.split('/')[-1]

    # Set up the request to the GitHub API
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github+json'
    }

    # Prepare the payload to add the issue to the project
    project_payload = {
        "content_id": issue_number,
        "content_type": "Issue"
    }

    project_api_url = f'https://api.github.com/projects/{project_id}/columns/cards'
    
    # Make the request
    response = requests.post(project_api_url, json=project_payload, headers=headers)
    
    if response.status_code == 201:
        print(f"Issue successfully added to the project.")
    else:
        print(f"Failed to add issue to project. Response: {response.text}")

# Main function
def main(csv_file, repo_name, token, project_id, include_assignee=False):
    # Authenticate to GitHub
    g = Github(token)
    repo = g.get_repo(repo_name)

    # Open and read the CSV file
    with open(csv_file, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            # Construct the issue title and body
            title = f"Test Failed: {row['Failed test']}"
            body = (
                f"### Failed test\n"
                f"- **Failed test**: {row['Failed test']}\n"
                f"- **Arch**: {row['Arch']}\n"
                f"- **Error message**: {row['Error message']}\n"
                f"- **Track**: {row['Track']}\n"
                f"- **Status**: {row['Status']}\n"
            )
            
            assignee = row['Assignee'] if include_assignee and 'Assignee' in row else None
            issue = create_github_issue(repo, title, body, assignee)
            
            # Add the created issue to the GitHub project
            add_issue_to_project(issue.html_url, project_id, token)

# Argument parser
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create GitHub issues from a CSV file and add them to a project.')
    parser.add_argument('csv_file', help='Path to the CSV file')
    parser.add_argument('repo_name', help='GitHub repository name (e.g., user/repo)')
    parser.add_argument('token', help='GitHub personal access token')
    parser.add_argument('project_id', help='GitHub project ID')
    parser.add_argument('--include_assignee', action='store_true', help='Flag to include assignee in the issue creation')
    
    args = parser.parse_args()
    main(args.csv_file, args.repo_name, args.token, args.project_id, args.include_assignee)
