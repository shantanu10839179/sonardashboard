import requests
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# GitHub API token and headers
GITHUB_TOKEN = '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'
HEADERS = {'Authorization': f'token {GITHUB_TOKEN}'}

# PostgreSQL connection details
DB_HOST = 'localhost'
DB_NAME ='github-actions-db'
DB_USER = 'postgres'
DB_PASS = 'postgres'
DB_PORT = "5432"

def fetch_pull_requests(repo, start_date, end_date):
    print(f"Fetching pull requests for {repo} from {start_date} to {end_date}")
    prs_url = f'https://api.github.com/repos/{repo}/pulls?state=all&since={start_date}'
    prs_response = requests.get(prs_url, headers=HEADERS)
    prs_data = prs_response.json()

    pr_metrics = []
    for pr in prs_data:
        pr_created_at = datetime.strptime(pr['created_at'], '%Y-%m-%dT%H:%M:%SZ')
        if pr_created_at > datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%SZ'):
            continue

        pr_metric = {
            'repo_name': repo,
            'start_date': start_date,
            'end_date': end_date,
            'pr_number': pr['number'],
            'state': pr['state'],
            'author': pr['user']['login'],
            'merged': pr['merged_at'] is not None,
            'merge_time': None,
            'review_time': None,
            'review_count': 0,
            'comment_count': 0,
            'additions': 0,
            'deletions': 0,
            'changed_files': 0
        }

        if pr_metric['merged']:
            pr_metric['merge_time'] = datetime.strptime(pr['merged_at'], '%Y-%m-%dT%H:%M:%SZ') - datetime.strptime(pr['created_at'], '%Y-%m-%dT%H:%M:%SZ')

        reviews_url = pr['url'] + '/reviews'
        reviews_response = requests.get(reviews_url, headers=HEADERS)
        reviews_data = reviews_response.json()
        pr_metric['review_count'] = len(reviews_data)
        if reviews_data:
            pr_metric['review_time'] = datetime.strptime(reviews_data[0]['submitted_at'], '%Y-%m-%dT%H:%M:%SZ') - datetime.strptime(pr['created_at'], '%Y-%m-%dT%H:%M:%SZ')

        comments_url = pr['url'] + '/comments'
        comments_response = requests.get(comments_url, headers=HEADERS)
        comments_data = comments_response.json()
        pr_metric['comment_count'] = len(comments_data)

        files_url = pr['url'] + '/files'
        files_response = requests.get(files_url, headers=HEADERS)
        files_data = files_response.json()
        pr_metric['changed_files'] = len(files_data)
        for file in files_data:
            pr_metric['additions'] += file['additions']
            pr_metric['deletions'] += file['deletions']

        pr_metrics.append(pr_metric)

    print(f"Fetched {len(pr_metrics)} pull requests for {repo} from {start_date} to {end_date}")
    return pr_metrics

def fetch_commits(repo, start_date, end_date):
    print(f"Fetching commits for {repo} from {start_date} to {end_date}")
    commits_url = f'https://api.github.com/repos/{repo}/commits?since={start_date}&until={end_date}'
    commits_response = requests.get(commits_url, headers=HEADERS)
    commits_data = commits_response.json()

    commit_metrics = []
    for commit in commits_data:
        commit_date = datetime.strptime(commit['commit']['author']['date'], '%Y-%m-%dT%H:%M:%SZ').date()
        commit_metric = {
            'repo_name': repo,
            'start_date': start_date,
            'end_date': end_date,
            'commit_date': commit_date.strftime('%Y-%m-%d'),  # Convert to string
            'commit_hash': commit['sha'],
            'commit_user': commit['commit']['author']['name'],
            'commit_message': commit['commit']['message'],
            'files_changed': 0,
            'additions': 0,
            'deletions': 0
        }

        commit_details_url = f'https://api.github.com/repos/{repo}/commits/{commit["sha"]}'
        commit_details_response = requests.get(commit_details_url, headers=HEADERS)
        commit_details_data = commit_details_response.json()
        files_data = commit_details_data.get('files', [])
        commit_metric['files_changed'] = len(files_data)
        for file in files_data:
            commit_metric['additions'] += file['additions']
            commit_metric['deletions'] += file['deletions']

        commit_metrics.append(commit_metric)

    print(f"Fetched {len(commit_metrics)} commits for {repo} from {start_date} to {end_date}")
    return commit_metrics

def store_pull_requests_in_db(pr_metrics):
    print(f"Storing {len(pr_metrics)} pull requests in the database")
    conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cursor = conn.cursor()
    insert_query = """
    INSERT INTO pr_details (repo_name, start_date, end_date, pr_number, state, author, merged, merge_time, review_time, review_count, comment_count, additions, deletions, changed_files)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    for pr_metric in pr_metrics:
        cursor.execute(insert_query, (pr_metric['repo_name'], pr_metric['start_date'], pr_metric['end_date'], pr_metric['pr_number'], pr_metric['state'], pr_metric['author'], pr_metric['merged'], pr_metric['merge_time'], pr_metric['review_time'], pr_metric['review_count'], pr_metric['comment_count'], pr_metric['additions'], pr_metric['deletions'], pr_metric['changed_files']))
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Stored {len(pr_metrics)} pull requests in the database")

def store_commits_in_db(commit_metrics):
    print(f"Storing {len(commit_metrics)} commits in the database")
    conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cursor = conn.cursor()
    insert_query = """
    INSERT INTO commit_details (repo_name, start_date, end_date, commit_date, commit_hash, commit_user, commit_message, files_changed, additions, deletions)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    for commit_metric in commit_metrics:
        print(f"Inserting commit: {commit_metric}")
        try:
            # Ensure all values are strings, and provide default values for integer columns
            sql_command = cursor.mogrify(insert_query, (
                str(commit_metric['repo_name']), 
                str(commit_metric['start_date']), 
                str(commit_metric['end_date']), 
                str(commit_metric['commit_date']), 
                str(commit_metric['commit_hash']),
                str(commit_metric['commit_user']),
                str(commit_metric['commit_message']),
                int(commit_metric['files_changed'] if commit_metric['files_changed'] is not None else 0),
                int(commit_metric['additions'] if commit_metric['additions'] is not None else 0),
                int(commit_metric['deletions'] if commit_metric['deletions'] is not None else 0)
            ))
            print(f"Executed SQL: {sql_command}")
            cursor.execute(sql_command)
        except Exception as e:
            print(f"Error inserting commit: {commit_metric}")
            print(e)
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Stored {len(commit_metrics)} commits in the database")

def main():
    repos = ["shantanu10839179/github-actions-lab", "shantanu10839179/devsecopsdashboard","shantanu10839179/test_sonar"]
    
    # ["grafana/grafana", "microsoft/TypeScript","fastapi/fastapi",
    #          "rvijaykumar74/github-actions-lab",
    #     "shantanu10839179/github-actions-lab", "shantanu10839179/devsecopsdashboard", 
    #     "shantanu10839179/test_sonar"]  # List of repositories
    start_date = datetime.strptime('2025-10-15', '%Y-%m-%d')
    end_date = datetime.strptime('2025-10-27', '%Y-%m-%d')

    current_date = start_date
    while current_date <= end_date:
        start_datetime = current_date.strftime('%Y-%m-%dT00:00:00Z')
        end_datetime = current_date.strftime('%Y-%m-%dT23:59:59Z')
        print(f"Processing data for {current_date.strftime('%Y-%m-%d')}")
        for repo in repos:
            pr_metrics = fetch_pull_requests(repo, start_datetime, end_datetime)
            store_pull_requests_in_db(pr_metrics)
            
            commit_metrics = fetch_commits(repo, start_datetime, end_datetime)
            store_commits_in_db(commit_metrics)
        
        current_date += timedelta(days=1)
        print(f"Completed processing for {current_date.strftime('%Y-%m-%d')}")

if __name__ == '__main__':
    main()