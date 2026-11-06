import json
import os
import re
from urllib.request import Request, urlopen
from .database import schema_text

EXAMPLES = {
    'Visits by facility': '''SELECT f.facility_name, SUM(d.visits) AS total_visits FROM daily_operations d JOIN facilities f ON f.facility_id=d.facility_id GROUP BY f.facility_name ORDER BY total_visits DESC''',
    'Monthly visits trend': '''SELECT substr(service_date,1,7) AS month, SUM(visits) AS total_visits FROM daily_operations GROUP BY substr(service_date,1,7) ORDER BY month''',
    'Average wait by facility': '''SELECT f.facility_name, ROUND(AVG(d.avg_wait_minutes),1) AS avg_wait_minutes FROM daily_operations d JOIN facilities f ON f.facility_id=d.facility_id GROUP BY f.facility_name ORDER BY avg_wait_minutes DESC''',
    'Expenses by region': '''SELECT f.region, ROUND(SUM(d.expenses),2) AS total_expenses FROM daily_operations d JOIN facilities f ON f.facility_id=d.facility_id GROUP BY f.region ORDER BY total_expenses DESC''',
    'Admissions by month': '''SELECT substr(service_date,1,7) AS month, SUM(admissions) AS admissions FROM daily_operations GROUP BY substr(service_date,1,7) ORDER BY month''',
}


def llm_sql(question, api_key, model='gpt-4o-mini'):
    if not api_key:
        raise ValueError('Provide an OpenAI API key for custom questions; sample questions work without a key.')
    prompt = ('You are a SQLite analyst. Return only a single SELECT query, no markdown. '
              'Use only the listed tables, no external data or functions. Limit detailed rows to 100. '
              'Never write INSERT, UPDATE, DELETE, PRAGMA, ATTACH, or DDL.\n'
              + schema_text() + '\nQuestion: ' + question[:1200])
    payload = json.dumps({'model':model,'messages':[{'role':'user','content':prompt}], 'temperature':0}).encode()
    req = Request('https://api.openai.com/v1/chat/completions', data=payload,
                  headers={'Authorization':f'Bearer {api_key}', 'Content-Type':'application/json'}, method='POST')
    with urlopen(req, timeout=30) as response:
        answer = json.load(response)['choices'][0]['message']['content'].strip()
    return re.sub(r'^```(?:sql)?\s*|\s*```$', '', answer, flags=re.I).strip()


def explain_result(question, columns, rows):
    if not rows:
        return 'The query returned no matching records.'
    return f'Returned {len(rows)} rows across {len(columns)} columns. Review the chart and table below; figures come from synthetic demonstration data.'
