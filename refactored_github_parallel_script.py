import os
import requests
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
DB_HOST = "localhost"
DB_USER = "postgres"
DB_PASS = "postgres"
DB_PORT = "5432"
DB_NAME = "github-actions-db"

GITHUB_REPOS = [
    "grafana/grafana",
    "microsoft/TypeScript",
    "fastapi/fastapi",
    "rvijaykumar74/github-actions-lab",
    "shantanu10839179/github-actions-lab",
    "shantanu10839179/devsecopsdashboard",
    "shantanu10839179/test_sonar",
    "shantanu10839179/sonardashboard"
]

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS,
            host=DB_HOST, port=DB_PORT
        )
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
                    failure_reason VARCHAR(255),
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
            INSERT INTO change_failure_rate_runs (repo_name, run_id, conclusion, completed_at, failure_reason)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (repo_name, run_id) DO UPDATE SET
                conclusion = EXCLUDED.conclusion,
                completed_at = EXCLUDED.completed_at,
                failure_reason = EXCLUDED.failure_reason;
        """
        cursor.executemany(insert_query, data)
        conn.commit()
        print(f"  - Upserted {len(data)} records for CFR/Build Count analysis.")

def insert_build_duration_data(conn, data):
    with conn.cursor() as cursor:
        insert_query = """
            INSERT INTO build_durations (repo_name, run_id, duration_in_seconds, completed_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (repo_name, run_id) DO UPDATE SET
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
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (repo_name, failed_run_id) DO NOTHING;
        """
        cursor.executemany(insert_query, data)
        conn.commit()
        print(f"  - Upserted {len(data)} records for MTTR analysis.")

def get_default_branch(repo):
    try:
        response = requests.get(f"https://api.github.com/repos/{repo}", headers=HEADERS)
        response.raise_for_status()
        return response.json().get('default_branch', 'main')
    except requests.exceptions.RequestException as e:
        print(f"Could not fetch default branch for {repo}: {e}")
        return 'main'

def get_all_workflow_runs(repo, branch=None):
    # Get all workflow runs (optionally filter by branch)
    runs_url = f"https://api.github.com/repos/{repo}/actions/runs?per_page=100"
    if branch:
        runs_url += f"&branch={branch}"
    try:
        response = requests.get(runs_url, headers=HEADERS)
        response.raise_for_status()
        workflow_runs = response.json().get('workflow_runs', [])
        print(f"    - Total workflow runs fetched for {repo}: {len(workflow_runs)}")
        return workflow_runs
    except requests.exceptions.RequestException as e:
        print(f"    - Could not fetch workflow runs for {repo}: {e}")
        return []

def process_repo(repo, default_branch, db_conn):
    print(f"  - Processing repository: {repo} (branch: {default_branch})")
    workflow_runs = get_all_workflow_runs(repo, default_branch)
    cfr_data = []
    duration_data = []
    mttr_data = []

    # Print all workflow runs for debug
    for run in workflow_runs:
        print(f"    - Run ID: {run.get('id')}, Status: {run.get('status')}, Conclusion: {run.get('conclusion')}, Name: {run.get('name')}, Created: {run.get('created_at')}, Updated: {run.get('updated_at')}, Head SHA: {run.get('head_sha')}")
        # For overnight/staging pipelines, you can filter by run name or scheduled trigger
        if run.get('event') == 'schedule':
            print(f"      [Scheduled Pipeline] {run.get('name')} ran at {run.get('created_at')} with status {run.get('conclusion')}")

    # Sort runs by completion time
    sorted_runs = sorted(workflow_runs, key=lambda r: r['updated_at'] or '', reverse=False)
    for i, run in enumerate(sorted_runs):
        try:
            completed_at = datetime.fromisoformat(run['updated_at'].replace('Z', '+00:00'))
            created_at = datetime.fromisoformat(run['created_at'].replace('Z', '+00:00'))
            duration = (completed_at - created_at).total_seconds()
            failure_reason = ""
            if run['conclusion'] == 'failure':
                # Try to get more details if available
                failure_reason = run.get('name', '')  # fallback to workflow name
            if run['conclusion'] in ['success', 'failure']:
                cfr_data.append((repo, run['id'], run['conclusion'], completed_at, failure_reason))
                duration_data.append((repo, run['id'], int(duration), completed_at))
            if run['conclusion'] == 'failure':
                next_success_run = None
                for subsequent_run in sorted_runs[i+1:]:
                    if subsequent_run['conclusion'] == 'success':
                        next_success_run = subsequent_run
                        break
                if next_success_run:
                    failure_time = completed_at
                    resolution_time = datetime.fromisoformat(next_success_run['updated_at'].replace('Z', '+00:00'))
                    time_to_recover = (resolution_time - failure_time).total_seconds()
                    if time_to_recover >= 0:
                        mttr_data.append((repo, run['id'], next_success_run['id'], failure_time, resolution_time, int(time_to_recover)))
        except Exception as e:
            print(f"    - Error processing run {run.get('id')}: {e}")

    if cfr_data:
        insert_cfr_data(db_conn, cfr_data)
    if duration_data:
        insert_build_duration_data(db_conn, duration_data)
    if mttr_data:
        insert_mttr_data(db_conn, mttr_data)

def main():
    db_connection = get_db_connection()
    if not db_connection:
        return
    setup_database(db_connection)

    # Parallelize repo processing
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(
                process_repo, repo, get_default_branch(repo), db_connection
            )
            for repo in GITHUB_REPOS
        ]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error processing repo: {e}")

    db_connection.close()
    print("\nProcess finished and database connection closed.")

if __name__ == "__main__":
    main()