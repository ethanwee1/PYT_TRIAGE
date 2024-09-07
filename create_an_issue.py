import csv
import argparse
from github import Github

# Function to create an issue on GitHub
def create_github_issue(repo, title, body, assignee=None):
    issue = repo.create_issue(title=title, body=body, assignee=assignee)
    print(f"Issue created: {issue.html_url}")

# Main function
def main(csv_file, repo_name, token, include_assignee=False):
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
            create_github_issue(repo, title, body, assignee)

# Argument parser
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create GitHub issues from a CSV file.')
    parser.add_argument('csv_file', help='Path to the CSV file')
    parser.add_argument('repo_name', help='GitHub repository name (e.g., user/repo)')
    parser.add_argument('token', help='GitHub personal access token')
    parser.add_argument('--include_assignee', action='store_true', help='Flag to include assignee in the issue creation')
    
    args = parser.parse_args()
    main(args.csv_file, args.repo_name, args.token, args.include_assignee)
