import os
import requests
import psycopg2
from datetime import datetime

# --- Configuration ---
GITHUB_TOKEN = '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'
HEADERS = {'Authorization': f'token {GITHUB_TOKEN}'}

# Database Connection Details
DB_HOST = 'localhost'
DB_NAME ='github-actions-db'
DB_USER = 'postgres'
DB_PASS = 'postgres'
DB_PORT = "5432"



# GitHub Repositories to analyze
GITHUB_REPOS = [
    "grafana/grafana",
    "microsoft/TypeScript",
    "fastapi/fastapi",
    "rvijaykumar74/github-actions-lab",
    "shantanu10839179/github-actions-lab","shantanu10839179/demo-repo", 
    "shantanu10839179/devsecopsdashboard", "shantanu10839179/test_sonar"
]

# GitHub API Configuration
# It's highly recommended to use a Personal Access Token
# to avoid rate limiting.
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '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')
if GITHUB_TOKEN == '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':
    print("Warning: For better rate limits, set your GITHUB_TOKEN environment variable or edit the script.")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# --- Database Functions ---

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except (Exception, psycopg2.Error) as error:
        print(f"Error while connecting to PostgreSQL: {error}")
        return None

def setup_database(conn):
    """Ensures the required table exists in the database."""
    try:
        cursor = conn.cursor()
        
        # SQL to create the table if it doesn't exist. This makes the script idempotent.
        create_table_query = """
        CREATE TABLE IF NOT EXISTS lead_time_to_change (
            id SERIAL PRIMARY KEY,
            repo_name VARCHAR(255) NOT NULL,
            pull_request_id INTEGER NOT NULL,
            first_commit_at TIMESTAMP WITH TIME ZONE,
            merged_at TIMESTAMP WITH TIME ZONE,
            lead_time_in_seconds INTEGER,
            UNIQUE(repo_name, pull_request_id)
        );
        """
        cursor.execute(create_table_query)
        conn.commit()
        cursor.close()
        print("Database setup complete. Table 'lead_time_to_change' is ready.")
    except (Exception, psycopg2.Error) as error:
        print(f"Error during database setup: {error}")


def insert_data_to_db(conn, data):
    """Inserts a list of lead time data into the PostgreSQL database."""
    try:
        cursor = conn.cursor()
        
        # Using ON CONFLICT to avoid errors if we run the script multiple times
        insert_query = """
            INSERT INTO lead_time_to_change (
                repo_name, pull_request_id, first_commit_at, merged_at, lead_time_in_seconds
            ) VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (repo_name, pull_request_id) DO UPDATE SET
                first_commit_at = EXCLUDED.first_commit_at,
                merged_at = EXCLUDED.merged_at,
                lead_time_in_seconds = EXCLUDED.lead_time_in_seconds;
        """
        
        cursor.executemany(insert_query, data)
        conn.commit()
        print(f"Successfully inserted/updated {len(data)} records.")
        cursor.close()

    except (Exception, psycopg2.Error) as error:
        print(f"Error while inserting data: {error}")

# --- GitHub API Functions ---

def get_first_commit_date(commits_url):
    """Fetches all commits for a PR and returns the date of the first one."""
    try:
        response = requests.get(commits_url, headers=HEADERS)
        response.raise_for_status()
        commits = response.json()
        if commits:
            # The first commit in the list is the oldest one for the PR
            first_commit_date_str = commits[0]['commit']['author']['date']
            return datetime.fromisoformat(first_commit_date_str.replace('Z', '+00:00'))
    except requests.exceptions.RequestException as e:
        print(f"Error fetching commits from {commits_url}: {e}")
    return None

def fetch_and_process_repos(conn):
    """Main function to fetch PRs from repos and process them."""
    for repo in GITHUB_REPOS:
        print(f"\n--- Processing repository: {repo} ---")
        
        # We fetch pull requests that are closed and have been merged.
        # We only look at PRs merged in the last 90 days as an example.
        # You can adjust this by changing `per_page` or adding date filters.
        api_url = f"https://api.github.com/repos/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page=100"
        
        try:
            response = requests.get(api_url, headers=HEADERS)
            response.raise_for_status() # Raises an exception for bad status codes
            pull_requests = response.json()

            lead_time_data = []

            for pr in pull_requests:
                # We only care about merged pull requests
                if pr.get('merged_at'):
                    pr_id = pr['number']
                    merged_at_str = pr['merged_at']
                    merged_at = datetime.fromisoformat(merged_at_str.replace('Z', '+00:00'))

                    # Get the date of the very first commit
                    commits_url = pr['commits_url']
                    first_commit_at = get_first_commit_date(commits_url)

                    if first_commit_at:
                        # Calculate lead time in seconds
                        lead_time = (merged_at - first_commit_at).total_seconds()
                        
                        if lead_time >= 0: # Ensure lead time is not negative
                            lead_time_data.append(
                                (repo, pr_id, first_commit_at, merged_at, int(lead_time))
                            )
                            print(f"  - PR #{pr_id}: Lead Time = {lead_time / 3600:.2f} hours")

            if lead_time_data:
                insert_data_to_db(conn, lead_time_data)
            else:
                print("No newly merged pull requests found to process.")

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for repo {repo}: {e}")
            if e.response:
                print(f"   Response: {e.response.status_code} - {e.response.text}")


if __name__ == "__main__":
    db_connection = get_db_connection()
    if db_connection:
        # 1. Ensure the database table exists
        setup_database(db_connection)
        
        # 2. Fetch data from GitHub and insert it into the table
        fetch_and_process_repos(db_connection)
        
        # 3. Close the connection
        db_connection.close()
        print("\nProcess finished and database connection closed.")