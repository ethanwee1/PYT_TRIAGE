import csv
import argparse
from github import Github
import requests
import sys
import os  # Import os to access environment variables

# Hardcoded GitHub organization project ID
project_id = "PVT_kwDOAULW6s4Am9UL"  # Replace with your actual project ID

# Read GitHub token from environment variable
token = os.environ.get('GITHUB_TOKEN')
if not token:
    print("Error: 'GITHUB_TOKEN' environment variable not set.")
    sys.exit(1)

# Function to get global node ID of an issue using the REST API
def get_issue_global_node_id(issue_url):
    issue_number = issue_url.split('/')[-1]
    repo_name = '/'.join(issue_url.split('/')[-4:-2])
    url = f"https://api.github.com/repos/{repo_name}/issues/{issue_number}"
    headers = {
        "Authorization": f"token {token}",
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

# Function to add an issue to an organization-level GitHub project
def add_issue_to_org_project(issue_global_node_id):
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
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
        "projectId": project_id,  # Using the hardcoded project ID
        "issueId": issue_global_node_id
    }
    response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
    
    if response.status_code == 200:
        print(f"Issue added to organization-level project: {response.json()}")
    else:
        print(f"Failed to add issue to organization-level project: {response.text}")

# Function to check for duplicate issues
def check_for_duplicates(repo, title):
    issues = repo.get_issues(state='open')
    for issue in issues:
        if issue.title == title:
            print(f"Duplicate found: {issue.html_url}")
            return True
    return False

# Main function
def main(csv_file, repo_name, docker_id):
    # Check if docker_id is provided
    if not docker_id:
        print("Error: 'docker_id' must be provided.")
        sys.exit(1)
    
    # Authenticate to GitHub
    g = Github(token)
    repo = g.get_repo(repo_name)

    # Open and read the CSV file
    with open(csv_file, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            # Ensure required fields are present and not empty
            required_fields = ['Failed test', 'Arch', 'Error message']
            for field in required_fields:
                if not row.get(field):
                    print(f"Error: '{field}' field is missing or empty in the CSV.")
                    sys.exit(1)
            
            # Replace '::' with ' ' in the 'Failed test' field
            row['Failed test'] = row['Failed test'].replace('::', ' ')
            
            # Construct the issue title and body based on the columns in your CSV
            title = f"({row.get('Test Config', 'N/A')}) {row['Failed test']}"
            body = (
                f"- **Failed test**: {row['Failed test']}\n"
                f"- **Arch**: {row['Arch']}\n"
                f"- **Error message**: {row['Error message']}\n"
                f"- **Track**: {row.get('Track', 'N/A')}\n"
                f"- **Status**: {row.get('status', 'N/A')}\n"
                f"- **Jira**: {row.get('jira', 'N/A')}\n"
                f"- **Docker ID**: {docker_id}\n"
            )
            
            # Check for duplicates before proceeding
            if check_for_duplicates(repo, title):
                print(f"Skipping issue creation for: {title} (duplicate found)")
                continue
            
            # Get the assignee from the CSV file
            assignee = row.get('assignee')
            
            # Create the issue
            issue = create_github_issue(repo, title, body, assignee)
            
            # Get the global node ID of the created issue
            issue_global_node_id = get_issue_global_node_id(issue.html_url)
            
            if issue_global_node_id:
                # Add the issue to the organization-level GitHub project
                add_issue_to_org_project(issue_global_node_id)

# Argument parser
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create GitHub issues from a CSV file and add them to an organization-level project.')
    parser.add_argument('csv_file', help='Path to the CSV file')
    parser.add_argument('repo_name', help='GitHub repository name (e.g., user/repo)')
    parser.add_argument('--docker_id', help='Docker ID to include in the issue description', required=False)
    
    args = parser.parse_args()
    main(args.csv_file, args.repo_name, args.docker_id)

