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

METRICS = [
    'coverage', 'bugs', 'vulnerabilities', 'code_smells', 'sqale_index', 'ncloc',
    'duplicated_lines_density', 'sqale_rating', 'reliability_rating', 'security_rating'
]

PROJECT_KEY = "shantanu10839179_sonardashboard"  # Update with your project key

def get_measures(project_key):
    url = f"{SONAR_HOST}/api/measures/component"
    params = {
        'component': project_key,
        'metricKeys': ','.join(METRICS),
        'organization': SONAR_ORG
    }
    resp = requests.get(url, headers=HEADERS, params=params)
    resp.raise_for_status()
    measures = {m['metric']: m.get('value') for m in resp.json().get('component', {}).get('measures', [])}
    return measures

def get_latest_analysis_date(project_key):
    url = f"{SONAR_HOST}/api/project_analyses/search"
    params = {'project': project_key, 'organization': SONAR_ORG}
    resp = requests.get(url, headers=HEADERS, params=params)
    resp.raise_for_status()
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

def insert_sonar_data(conn, row):
    with conn.cursor() as cursor:
        insert_query = """
        INSERT INTO sonarqube_results (
            repo_name, project_key, analysis_date, coverage, bugs, vulnerabilities, code_smells,
            technical_debt_minutes, lines_of_code, duplicated_lines, maintainability_rating,
            reliability_rating, security_rating, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (repo_name, project_key, analysis_date) DO NOTHING;
        """
        cursor.execute(insert_query, row)
        conn.commit()

def main():
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
    )
    repo_name = PROJECT_KEY.replace("_", "/", 1)
    measures = get_measures(PROJECT_KEY)
    analysis_date = get_latest_analysis_date(PROJECT_KEY)
    row = (
        repo_name,
        PROJECT_KEY,
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
        safe_int(measures.get('security_rating')),
        datetime.now()
    )
    insert_sonar_data(conn, row)
    conn.close()
    print("Done.")

if __name__ == "__main__":
    main()