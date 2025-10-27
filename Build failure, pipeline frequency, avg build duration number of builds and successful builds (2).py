import os
import requests
import psycopg2
from datetime import datetime

# --- Configuration ---

# Database Connection Details
DB_HOST = "localhost"
DB_NAME ='github-actions-db'
DB_USER = "postgres"
DB_PASS = "postgres"
DB_PORT = "5432"

# GitHub Repositories to analyze
GITHUB_REPOS = [
["grafana/grafana", "microsoft/TypeScript","fastapi/fastapi","rvijaykumar74/github-actions-lab","shantanu10839179/github-actions-lab", "shantanu10839179/devsecopsdashboard","shantanu10839179/test_sonar"] 
]

# GitHub API Configuration
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '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')
if GITHUB_TOKEN == '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':
    print("CRITICAL: GitHub token not found. The script will likely fail to fetch Actions data.")
    print("Please edit the script to add your Personal Access Token.")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# --- Database Functions (No Changes) ---

def get_db_connection():
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
        return conn
    except (Exception, psycopg2.Error) as error:
        print(f"Error while connecting to PostgreSQL: {error}")
        return None

def setup_database(conn):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS change_failure_rate_runs (
                id SERIAL PRIMARY KEY,
                repo_name VARCHAR(255) NOT NULL,
                run_id BIGINT NOT NULL,
                conclusion VARCHAR(50),
                completed_at TIMESTAMP WITH TIME ZONE,
                UNIQUE(repo_name, run_id)
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS build_durations (
                id SERIAL PRIMARY KEY,
                repo_name VARCHAR(255) NOT NULL,
                run_id BIGINT NOT NULL,
                duration_in_seconds INTEGER,
                completed_at TIMESTAMP WITH TIME ZONE,
                UNIQUE(repo_name, run_id)
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS incidents_for_mttr (
                id SERIAL PRIMARY KEY,
                repo_name VARCHAR(255) NOT NULL,
                failed_run_id BIGINT NOT NULL,
                resolved_run_id BIGINT,
                failure_time TIMESTAMP WITH TIME ZONE,
                resolution_time TIMESTAMP WITH TIME ZONE,
                time_to_recover_in_seconds INTEGER,
                UNIQUE(repo_name, failed_run_id)
            );
            """)
        conn.commit()
        print("Database setup complete. All tables are ready.")
    except (Exception, psycopg2.Error) as error:
        print(f"Error during database setup: {error}")

def insert_cfr_data(conn, data):
    with conn.cursor() as cursor:
        insert_query = """
            INSERT INTO change_failure_rate_runs (repo_name, run_id, conclusion, completed_at)
            VALUES (%s, %s, %s, %s) ON CONFLICT (repo_name, run_id) DO UPDATE SET
                conclusion = EXCLUDED.conclusion,
                completed_at = EXCLUDED.completed_at;
        """
        cursor.executemany(insert_query, data)
        conn.commit()
    print(f"  - Upserted {len(data)} records for CFR/Build Count analysis.")

def insert_build_duration_data(conn, data):
    with conn.cursor() as cursor:
        insert_query = """
            INSERT INTO build_durations (repo_name, run_id, duration_in_seconds, completed_at)
            VALUES (%s, %s, %s, %s) ON CONFLICT (repo_name, run_id) DO UPDATE SET
                duration_in_seconds = EXCLUDED.duration_in_seconds,
                completed_at = EXCLUDED.completed_at;
        """
        cursor.executemany(insert_query, data)
        conn.commit()
    print(f"  - Upserted {len(data)} records for Build Duration analysis.")

def insert_mttr_data(conn, data):
    with conn.cursor() as cursor:
        insert_query = """
            INSERT INTO incidents_for_mttr (repo_name, failed_run_id, resolved_run_id, failure_time, resolution_time, time_to_recover_in_seconds)
            VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (repo_name, failed_run_id) DO NOTHING;
        """
        cursor.executemany(insert_query, data)
        conn.commit()
    print(f"  - Upserted {len(data)} records for MTTR analysis.")

# --- GitHub API and Processing Logic (Completely Revised) ---

def get_default_branch(repo):
    try:
        response = requests.get(f"https://api.github.com/repos/{repo}", headers=HEADERS)
        response.raise_for_status()
        return response.json().get('default_branch', 'main')
    except requests.exceptions.RequestException as e:
        print(f"Could not fetch default branch for {repo}: {e}")
        return 'main'

def get_runs_for_commits(repo, commits):
    """For a list of commit SHAs, find the associated completed workflow runs."""
    commit_to_run_map = {}
    print(f"  - Searching for workflow runs for {len(commits)} commits...")
    for commit_sha in commits:
        try:
            # This endpoint finds all runs for a specific commit
            run_url = f"https://api.github.com/repos/{repo}/commits/{commit_sha}/check-runs"
            response = requests.get(run_url, headers=HEADERS)
            response.raise_for_status()
            check_runs = response.json().get('check_runs', [])
            
            # We only care about completed CI runs from GitHub Actions
            for run in check_runs:
                if run.get('app', {}).get('slug') == 'github-actions' and run.get('status') == 'completed':
                    # We found the run for this commit, store it and move to the next commit
                    commit_to_run_map[commit_sha] = run
                    break
        except requests.exceptions.RequestException as e:
            print(f"    - Could not fetch runs for commit {commit_sha[:7]}: {e}")
            continue
    return commit_to_run_map

def process_repo(repo, default_branch):
    """Main processing logic for a single repository."""
    # Step 1: Get recently merged PRs that targeted the default branch
    print(f"  - Finding recently merged pull requests targeted at '{default_branch}'...")
    pr_url = f"https://api.github.com/repos/{repo}/pulls?state=closed&base={default_branch}&sort=updated&direction=desc&per_page=100"
    
    try:
        response = requests.get(pr_url, headers=HEADERS)
        response.raise_for_status()
        all_prs = response.json()
        
        # Filter for only those that were actually merged
        merged_prs = [pr for pr in all_prs if pr.get('merged_at')]
        if not merged_prs:
            print("  - No recently merged PRs found.")
            return [], [], []
            
        print(f"  - Found {len(merged_prs)} merged PRs. Extracting commit SHAs.")
        commits = {pr['head']['sha']: pr for pr in merged_prs}

        # Step 2: For each merged PR's commit, find its corresponding workflow run
        commit_to_run_map = get_runs_for_commits(repo, commits.keys())
        if not commit_to_run_map:
            print("  - Could not find any associated workflow runs for the merged PRs.")
            return [], [], []

        print(f"  - Found {len(commit_to_run_map)} associated workflow runs. Processing data.")
        
        # Step 3: Process the runs we found into data for our DB tables
        cfr_data = []
        duration_data = []
        mttr_data = [] # MTTR logic remains difficult without a full timeline, focusing on CFR/Builds for now

        # Sort runs by completion time for MTTR logic
        sorted_runs = sorted(commit_to_run_map.values(), key=lambda r: r['completed_at'])
        
        for i, run in enumerate(sorted_runs):
            completed_at = datetime.fromisoformat(run['completed_at'].replace('Z', '+00:00'))
            created_at = datetime.fromisoformat(run['started_at'].replace('Z', '+00:00'))
            duration = (completed_at - created_at).total_seconds()
            
            if run['conclusion'] in ['success', 'failure']:
                cfr_data.append((repo, run['id'], run['conclusion'], completed_at))
                duration_data.append((repo, run['id'], int(duration), completed_at))

            # MTTR logic: Find time from this failure to the next success in our list of merged PRs
            if run['conclusion'] == 'failure':
                next_success_run = None
                for subsequent_run in sorted_runs[i+1:]:
                    if subsequent_run['conclusion'] == 'success':
                        next_success_run = subsequent_run
                        break
                
                if next_success_run:
                    failure_time = completed_at
                    resolution_time = datetime.fromisoformat(next_success_run['completed_at'].replace('Z', '+00:00'))
                    time_to_recover = (resolution_time - failure_time).total_seconds()
                    if time_to_recover >= 0:
                        mttr_data.append((repo, run['id'], next_success_run['id'], failure_time, resolution_time, int(time_to_recover)))
        
        return cfr_data, duration_data, mttr_data

    except requests.exceptions.RequestException as e:
        print(f"  - ERROR: Failed to process repo {repo}: {e}")
        return [], [], []

def main():
    db_connection = get_db_connection()
    if not db_connection:
        return
    
    setup_database(db_connection)

    for repo in GITHUB_REPOS:
        print(f"\n--- Processing repository: {repo} ---")
        default_branch = get_default_branch(repo)
        print(f"  - Using default branch: '{default_branch}'")
        
        cfr_data, duration_data, mttr_data = process_repo(repo, default_branch)

        if cfr_data:
            insert_cfr_data(db_connection, cfr_data)
        
        if duration_data:
            insert_build_duration_data(db_connection, duration_data)

        if mttr_data:
            insert_mttr_data(db_connection, mttr_data)

    db_connection.close()
    print("\nProcess finished and database connection closed.")

if __name__ == "__main__":
    main()