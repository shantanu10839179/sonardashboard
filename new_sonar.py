import os
import requests
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()
SONAR_TOKEN = os.environ.get('SONAR_TOKEN')
SONAR_ORG = os.environ.get('SONAR_ORGANIZATION', 'your_org')
SONAR_HOST = os.environ.get('SONAR_HOST_URL', "https://sonarcloud.io")
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'postgres')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASS', 'postgres')
DB_PORT = os.environ.get('DB_PORT', '5432')

HEADERS = {'Authorization': f'Bearer {SONAR_TOKEN}'}

# Only valid SonarQube metric keys (add more if needed)
METRICS = [
    'coverage', 'branch_coverage', 'line_coverage', 'new_coverage',
    'bugs', 'new_bugs', 'vulnerabilities', 'new_vulnerabilities',
    'code_smells', 'new_code_smells', 'sqale_index', 'ncloc',
    'duplicated_lines_density', 'new_duplicated_lines_density',
    'duplicated_lines', 'lines', 'new_lines',
    'maintainability_rating', 'new_maintainability_rating',
    'reliability_rating', 'new_reliability_rating',
    'security_rating', 'new_security_rating',
    'blocker_violations', 'critical_violations', 'major_violations', 'minor_violations', 'info_violations',
    'tests', 'test_errors', 'test_failures', 'test_execution_time', 'test_success_density',
    'comment_lines_density', 'complexity', 'functions', 'statements', 'classes', 'files',
    'new_lines_to_cover', 'new_uncovered_lines', 'new_violations'
]

PROJECT_KEYS = [
    "shantanu10839179_github-actions-lab",
    "shantanu10839179_devsecopsdashboard",
    "shantanu10839179_test_sonar"
]

def get_branches(project_key):
    url = f"{SONAR_HOST}/api/project_branches/list"
    params = {'project': project_key, 'organization': SONAR_ORG}
    resp = requests.get(url, headers=HEADERS, params=params)
    if resp.status_code == 404:
        print(f"Project {project_key} not found in organization {SONAR_ORG}. Skipping.")
        return []
    resp.raise_for_status()
    return [b['name'] for b in resp.json().get('branches', [])]

def get_analyses(project_key, branch):
    url = f"{SONAR_HOST}/api/project_analyses/search"
    params = {'project': project_key, 'branch': branch, 'organization': SONAR_ORG, 'ps': 100}
    resp = requests.get(url, headers=HEADERS, params=params)
    if resp.status_code == 404:
        print(f"No analyses found for {project_key} branch {branch}. Skipping.")
        return []
    resp.raise_for_status()
    return resp.json().get('analyses', [])

def get_measures(project_key, branch):
    url = f"{SONAR_HOST}/api/measures/component"
    params = {
        'component': project_key,
        'branch': branch,
        'metricKeys': ','.join(METRICS),
        'organization': SONAR_ORG
    }
    resp = requests.get(url, headers=HEADERS, params=params)
    if resp.status_code == 404:
        print(f"Metrics not found for {project_key} branch {branch}. Skipping.")
        return {}
    resp.raise_for_status()
    measures = {m['metric']: m.get('value') for m in resp.json().get('component', {}).get('measures', [])}
    return measures

def get_quality_gate_status(project_key, branch):
    url = f"{SONAR_HOST}/api/qualitygates/project_status"
    params = {
        'projectKey': project_key,
        'branch': branch,
        'organization': SONAR_ORG
    }
    resp = requests.get(url, headers=HEADERS, params=params)
    if resp.status_code == 404:
        return None, None
    resp.raise_for_status()
    data = resp.json()
    return data.get('projectStatus', {}).get('qualityGateStatus'), data.get('projectStatus', {}).get('alertStatus')

def insert_sonar_data(conn, row):
    with conn.cursor() as cursor:
        insert_query = """
        INSERT INTO sonarqube_results (
            repo_name, project_key, analysis_date, branch, quality_gate_status, alert_status, coverage, bugs, vulnerabilities, code_smells,
            sqale_index, ncloc, duplicated_lines_density, duplicated_lines, lines, maintainability_rating, reliability_rating,
            security_rating, blocker_violations, critical_violations, major_violations, minor_violations, info_violations,
            tests, test_errors, test_failures, test_execution_time, test_success_density, comment_lines_density, complexity,
            functions, statements, classes, files, branch_coverage, line_coverage, new_coverage, new_bugs, new_vulnerabilities,
            new_code_smells, new_duplicated_lines_density, new_lines, new_maintainability_rating, new_reliability_rating,
            new_security_rating, new_lines_to_cover, new_uncovered_lines, new_violations, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (repo_name, project_key, analysis_date, branch) DO NOTHING;
        """
        cursor.execute(insert_query, row)
        conn.commit()

def main():
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
    )
    for project_key in PROJECT_KEYS:
        repo_name = project_key.replace("_", "/", 1)
        branches = get_branches(project_key)
        for branch in branches:
            analyses = get_analyses(project_key, branch)
            for analysis in analyses:
                analysis_date = analysis.get('date')
                measures = get_measures(project_key, branch)
                quality_gate_status, alert_status = get_quality_gate_status(project_key, branch)
                row = (
                    repo_name, project_key, analysis_date, branch, quality_gate_status, alert_status,
                    measures.get('coverage'), measures.get('bugs'), measures.get('vulnerabilities'),
                    measures.get('code_smells'), measures.get('sqale_index'), measures.get('ncloc'),
                    measures.get('duplicated_lines_density'), measures.get('duplicated_lines'), measures.get('lines'),
                    measures.get('maintainability_rating'), measures.get('reliability_rating'), measures.get('security_rating'),
                    measures.get('blocker_violations'), measures.get('critical_violations'), measures.get('major_violations'),
                    measures.get('minor_violations'), measures.get('info_violations'), measures.get('tests'), measures.get('test_errors'),
                    measures.get('test_failures'), measures.get('test_execution_time'), measures.get('test_success_density'),
                    measures.get('comment_lines_density'), measures.get('complexity'), measures.get('functions'), measures.get('statements'),
                    measures.get('classes'), measures.get('files'), measures.get('branch_coverage'), measures.get('line_coverage'),
                    measures.get('new_coverage'), measures.get('new_bugs'), measures.get('new_vulnerabilities'), measures.get('new_code_smells'),
                    measures.get('new_duplicated_lines_density'), measures.get('new_lines'), measures.get('new_maintainability_rating'),
                    measures.get('new_reliability_rating'), measures.get('new_security_rating'), measures.get('new_lines_to_cover'),
                    measures.get('new_uncovered_lines'), measures.get('new_violations'), datetime.now()
                )
                insert_sonar_data(conn, row)
    conn.close()

if __name__ == "__main__":
    main()