import sqlite3
import sqlglot
from sqlglot import exp

ALLOWED_TABLES = {'facilities', 'daily_operations'}
BLOCKED = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create, exp.Alter, exp.Command, exp.Copy, exp.Attach, exp.Pragma, exp.Merge)


def validate_sql(sql: str) -> str:
    if not sql or len(sql) > 12000:
        raise ValueError('Missing or overly long SQL')
    try:
        statements = sqlglot.parse(sql, read='sqlite')
    except Exception as exc:
        raise ValueError('Invalid SQL syntax') from exc
    if len(statements) != 1 or statements[0] is None:
        raise ValueError('Only one SQL statement is permitted')
    tree = statements[0]
    if not isinstance(tree, (exp.Select, exp.Union, exp.Except, exp.Intersect)):
        raise ValueError('Only SELECT queries are permitted')
    if any(isinstance(node, BLOCKED) for node in tree.walk()):
        raise ValueError('Unsafe SQL operation')
    cte_names = {cte.alias.lower() for cte in tree.find_all(exp.CTE)}
    for table in tree.find_all(exp.Table):
        if table.name.lower() not in ALLOWED_TABLES | cte_names:
            raise ValueError(f'Table not permitted: {table.name}')
    # Exclude file-reading table-valued functions and any SQL functions not on this allowlist.
    safe_functions = {'COUNT','SUM','AVG','MIN','MAX','ROUND','ABS','COALESCE','NULLIF','DATE','STRFTIME','CAST','SUBSTR','LENGTH','UPPER','LOWER','IFNULL','TOTAL','JULIANDAY'}
    for node in tree.walk():
        if isinstance(node, exp.Anonymous) and node.name.upper() not in safe_functions:
            raise ValueError(f'Function not permitted: {node.name}')
    return tree.sql(dialect='sqlite')


def execute_readonly(db_path, sql, max_rows=300):
    safe = validate_sql(sql)
    uri = f'file:{db_path}?mode=ro'
    with sqlite3.connect(uri, uri=True) as con:
        con.execute('PRAGMA query_only=ON')
        con.set_progress_handler(lambda: 1, 100000)
        cursor = con.execute(f'SELECT * FROM ({safe}) AS validated_query LIMIT ?', (max_rows,))
        return [col[0] for col in cursor.description], cursor.fetchall()
