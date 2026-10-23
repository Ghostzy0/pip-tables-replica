"""Bounded local conversation; no model or network requests."""
import json
import os
import re
import tempfile
import threading
from pathlib import Path
from pip_tables.engine import Project, _ident, _json_value


class Session:
    def __init__(self, project):
        self.project = project
        self.path = project.path / 'replica.json'
        self.cancelled = threading.Event()
        self.messages = []
        self.table = None
        if self.path.exists():
            if self.path.stat().st_size > 4 * 1024**2:
                raise ValueError('Conversation exceeds 4 MB')
            data = json.loads(self.path.read_text())
            if not isinstance(data, dict) or data.get('version') != 1 or not isinstance(data.get('messages'), list):
                raise ValueError('Unsupported conversation sidecar')
            if len(data['messages']) > 40:
                raise ValueError('Conversation exceeds 40 messages')
            if data.get('table') is not None and not isinstance(data.get('table'), str):
                raise ValueError('Invalid selected table')
            for item in data['messages']:
                if not isinstance(item, dict) or item.get('kind') not in ('file', 'answer'):
                    raise ValueError('Invalid conversation entry')
                required = ('text', 'table') if item['kind'] == 'file' else ('question', 'sql', 'columns', 'rows', 'total', 'chart', 'source')
                if any(key not in item for key in required):
                    raise ValueError('Incomplete conversation entry')
                if item['kind'] == 'file' and (not all(isinstance(item[k], str) for k in required)
                        or any(len(item[k]) > 10_000 for k in required)):
                    raise ValueError('Invalid source card')
                if item['kind'] == 'answer' and (not isinstance(item['sql'], str) or not isinstance(item['question'], str)
                        or len(item['sql']) > 1_000_000 or len(item['question']) > 10_000
                        or not isinstance(item['columns'], list) or len(item['columns']) > 512
                        or not all(isinstance(c,str) and len(c) <= 10_000 for c in item['columns'])
                        or not isinstance(item['rows'], list) or len(item['rows']) > 1000
                        or any(not isinstance(r,list) or len(r) != len(item['columns']) for r in item['rows'])
                        or isinstance(item['total'], bool) or not isinstance(item['total'], int) or item['total'] < 0
                        or not isinstance(item['chart'], bool)
                        or (item['source'] is not None and (not isinstance(item['source'], str) or len(item['source']) > 10_000))):
                    raise ValueError('Invalid answer artifact')
            self.messages = data['messages']
            self.table = data.get('table')
        tables = project.tables()
        names = {t['name'] for t in tables}
        self.table = self.table if self.table in names else None
        represented = {m['table'] for m in self.messages if m['kind'] == 'file'}
        for table in tables:
            if table['name'] not in represented:
                self.messages.append({'kind': 'file', 'text': table['source'] + ' (recovered import)', 'table': table['name']})
        self.messages = self.messages[-40:]

    def save(self):
        data = json.dumps({'version': 1, 'table': self.table, 'messages': self.messages[-40:]}, default=_json_value)
        if len(data.encode()) > 4 * 1024**2:
            raise ValueError('Conversation exceeds 4 MB; start a new project')
        fd, name = tempfile.mkstemp(dir=self.project.path, prefix='.replica-', suffix='.tmp')
        try:
            with os.fdopen(fd, 'w') as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(name, self.path)
        finally:
            if os.path.exists(name): os.unlink(name)

    def record(self, message):
        previous = self.messages
        self.messages = (previous + [message])[-40:]
        try:
            self.save()
        except Exception:
            self.messages = previous
            raise

    def import_file(self, path):
        name = self.project.import_file(path)
        # Engine returns the actual collision-safe imported table name.
        previous = self.table
        self.table = name
        try:
            self.record({'kind': 'file', 'text': Path(path).name, 'table': name})
        except Exception as exc:
            self.table = previous
            raise OSError(f'Imported as {name}, but the conversation could not be saved; the table remains in the project and will be recovered when reopened') from exc
        return name

    def paste(self, text):
        if not text.strip() or len(text.encode()) > 2 * 1024**2:
            raise ValueError('Paste CSV between 1 byte and 2 MB')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'pasted_data.csv'
            path.write_text(text, encoding='utf-8')
            return self.import_file(path)

    def sql_for(self, prompt):
        if len(prompt) > 10000: raise ValueError('Question exceeds 10,000 characters')
        if prompt.lstrip().lower().startswith('sql:'):
            return prompt.split(':', 1)[1].strip(), False
        if not self.table: raise ValueError('Add a file or paste CSV first')
        table = next(t for t in self.project.tables() if t['name'] == self.table)
        cols = {c['name'].lower(): c['name'] for c in table['columns']}
        p = prompt.lower().strip()
        # Deliberately exact vocabulary, never silently guess a different column.
        if p in ('count rows', 'row count'):
            return f'SELECT count(*) AS rows FROM {_ident(self.table)}', False
        if p in ('preview', 'show data'):
            return f'SELECT * FROM {_ident(self.table)} LIMIT 20', False
        m = re.fullmatch(r'(sum|count|nulls) ([a-zA-Z_][\w ]*?)(?: by ([a-zA-Z_][\w ]*?))?(?: bar chart)?', p)
        if not m:
            raise ValueError('Supported: count rows; preview; sum amount; count amount; nulls amount; sum amount by region bar chart; or SQL: SELECT …')
        op, column, group = m.groups()
        if column not in cols or (group and group not in cols):
            raise ValueError('Use an exact imported column name; see the file preview')
        c = _ident(cols[column]); t = _ident(self.table)
        expr = {'sum': f'sum({c})', 'count': f'count({c})', 'nulls': f'count(*) - count({c})'}[op]
        alias = f'{op}_{column.replace(" ", "_")}'
        if group:
            g = _ident(cols[group])
            return f'SELECT {g}, {expr} AS {_ident(alias)} FROM {t} GROUP BY {g} ORDER BY {g}', True
        return f'SELECT {expr} AS {_ident(alias)} FROM {t}', False

    def ask(self, prompt):
        sql, chart = self.sql_for(prompt)
        provenance = 'Imported tables referenced by manual SQL' if prompt.lstrip().lower().startswith('sql:') else self.table
        if self.cancelled.is_set(): raise InterruptedError('Analysis stopped')
        result = self.project.query(sql, limit=1000)
        if self.cancelled.is_set(): raise InterruptedError('Analysis stopped')
        message = {'kind': 'answer', 'question': prompt, 'sql': sql, 'columns': result.columns,
                   'rows': _json_value(result.rows), 'total': result.total, 'chart': chart,
                   'source': provenance, 'elapsed': result.elapsed}
        self.record(message)
        return message
