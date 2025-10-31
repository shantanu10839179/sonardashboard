import os
import requests
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()
SONAR_TOKEN = os.environ.get('SONAR_TOKEN')
SONAR_ORG = os.environ.get('SONAR_ORGANIZATION', 'shantanu10839179')
SONAR_HOST = os.environ.get('SONAR_HOST_URL', "https://sonarcloud.io")
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'postgres')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASS', 'postgres')
DB_PORT = os.environ.get('DB_PORT', '5432')

HEADERS = {'Authorization': f'Bearer {SONAR_TOKEN}'}

# Use only valid metric keys for SonarCloud
METRICS = [
    'coverage', 'bugs', 'vulnerabilities', 'code_smells',
    'sqale_index', 'ncloc', 'duplicated_lines_density',
    'sqale_rating', 'reliability_rating', 'security_rating'
]

# List your SonarCloud project keys here (add/remove as needed)
PROJECT_KEYS = [
    "grafana_grafana",
    "microsoft_TypeScript",
    "fastapi_fastapi",
    "rvijaykumar74_github-actions-lab",
    "shantanu10839179_github-actions-lab",
    "shantanu10839179_devsecopsdashboard",
    "shantanu10839179_test_sonar"
]

def get_project_measures(project_key):
    url = f"{SONAR_HOST}/api/measures/component"
    params = {
        'component': project_key,
        'metricKeys': ','.join(METRICS),
        'organization': SONAR_ORG
    }
    resp = requests.get(url, headers=HEADERS, params=params)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    measures = {m['metric']: m.get('value') for m in resp.json().get('component', {}).get('measures', [])}
    return measures

def get_latest_analysis_date(project_key):
    url = f"{SONAR_HOST}/api/project_analyses/search"
    params = {'project': project_key, 'organization': SONAR_ORG}
    resp = requests.get(url, headers=HEADERS, params=params)
    if resp.status_code != 200:
        return None
    data = resp.json()
    if data.get('analyses'):
        return data['analyses'][0]['date']
    return None

def safe_float(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return None

def safe_int(val):
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return None

def setup_database(conn):
    with conn.cursor() as cursor:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sonarqube_results (
            id SERIAL PRIMARY KEY,
            repo_name VARCHAR(255) NOT NULL,
            project_key VARCHAR(255) NOT NULL,
            analysis_date TIMESTAMP WITH TIME ZONE,
            coverage DECIMAL(5,2),
            bugs INTEGER,
            vulnerabilities INTEGER,
            code_smells INTEGER,
            technical_debt_minutes INTEGER,
            lines_of_code INTEGER,
            duplicated_lines DECIMAL(5,2),
            maintainability_rating INTEGER,
            reliability_rating INTEGER,
            security_rating INTEGER,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()

def insert_sonar_data(conn, data):
    with conn.cursor() as cursor:
        insert_query = """
        INSERT INTO sonarqube_results (
            repo_name, project_key, analysis_date, coverage, bugs, vulnerabilities, code_smells,
            technical_debt_minutes, lines_of_code, duplicated_lines, maintainability_rating,
            reliability_rating, security_rating
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (repo_name, project_key, analysis_date) DO NOTHING;
        """
        cursor.executemany(insert_query, data)
        conn.commit()

def main():
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
    )
    setup_database(conn)

    all_data = []
    for project_key in PROJECT_KEYS:
        # Try to infer repo_name from project_key (for GitHub projects)
        if "_" in project_key:
            repo_name = project_key.replace("_", "/", 1)
        else:
            repo_name = project_key
        print(f"Processing {project_key} ({repo_name})...")
        measures = get_project_measures(project_key)
        if not measures:
            print(f"  No measures found for {project_key}")
            continue
        analysis_date = get_latest_analysis_date(project_key)
        row = (
            repo_name,
            project_key,
            analysis_date,
            safe_float(measures.get('coverage')),
            safe_int(measures.get('bugs')),
            safe_int(measures.get('vulnerabilities')),
            safe_int(measures.get('code_smells')),
            safe_int(measures.get('sqale_index')),
            safe_int(measures.get('ncloc')),
            safe_float(measures.get('duplicated_lines_density')),
            safe_int(measures.get('sqale_rating')),
            safe_int(measures.get('reliability_rating')),
            safe_int(measures.get('security_rating'))
        )
        all_data.append(row)

    if all_data:
        insert_sonar_data(conn, all_data)
        print(f"Inserted {len(all_data)} records into the database.")
    else:
        print("No SonarQube data to insert.")

    conn.close()
    print("Done.")

if __name__ == "__main__":
    main()