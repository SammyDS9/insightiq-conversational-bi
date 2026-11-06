import sqlite3
import pytest
from src.database import initialize
from src.security import validate_sql, execute_readonly
from src.assistant import EXAMPLES

@pytest.fixture
def db(tmp_path):
    return initialize(tmp_path/'test.db')

def test_database_seed(db):
    with sqlite3.connect(db) as con:
        assert con.execute('SELECT COUNT(*) FROM daily_operations').fetchone()[0] == 1460

def test_examples(db):
    for query in EXAMPLES.values():
        columns, rows = execute_readonly(db, query)
        assert columns and rows

@pytest.mark.parametrize('sql', ['DROP TABLE facilities', 'DELETE FROM daily_operations', 'SELECT * FROM sqlite_master', 'SELECT * FROM facilities; SELECT * FROM daily_operations', 'SELECT load_extension(\'x\')'])
def test_unsafe_sql_rejected(sql):
    with pytest.raises(ValueError): validate_sql(sql)

def test_select_allowed(db):
    cols, rows = execute_readonly(db, 'SELECT COUNT(*) AS n FROM facilities')
    assert rows[0][0] == 4
