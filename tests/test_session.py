import tempfile
import unittest
from pathlib import Path
from pip_tables.engine import Project
from tables_replica.session import Session

class Workflow(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.path=Path(self.tmp.name)/'project'
        self.project=Project.create(self.path); self.session=Session(self.project)
        self.session.paste('region,amount\nNorth,555.75\nSouth,419.75\nWest,408.75\nWest,\n')
    def tearDown(self): self.project.close(); self.tmp.cleanup()
    def test_workflow_and_reopen_export(self):
        answer=self.session.ask('sum amount by region bar chart')
        self.assertTrue(answer['chart']); self.assertEqual([str(r[1]) for r in answer['rows']],['555.75','419.75','408.75'])
        self.assertEqual(str(self.session.ask('sum amount')['rows'][0][0]),'1384.25')
        self.assertEqual(self.session.ask('nulls amount')['rows'],[[1]])
        reopened=Session(self.project); self.assertEqual(len(reopened.messages),4)
        dest=Path(self.tmp.name)/'out.csv'; self.project.export(answer['sql'],dest,'csv')
        self.assertIn('555.75',dest.read_text())
    def test_twelve_row_reference_oracle(self):
        self.session.import_file(Path(__file__).parents[1]/'examples'/'orders.csv')
        self.assertEqual(self.session.ask('count rows')['rows'],[[12]])
        self.assertEqual(self.session.ask('count amount')['rows'],[[11]])
        self.assertEqual(str(self.session.ask('sum amount')['rows'][0][0]),'1384.25')
        self.assertEqual([str(r[1]) for r in self.session.ask('sum amount by region bar chart')['rows']],['555.75','419.75','408.75'])
    def test_error_preserves_artifact(self):
        self.session.ask('count rows'); before=list(self.session.messages)
        for prompt in ['invent a forecast','sum missing','SQL: DROP TABLE pasted_data']:
            with self.assertRaises(Exception): self.session.ask(prompt)
            self.assertEqual(self.session.messages,before)
    def test_cancel_no_answer(self):
        before=len(self.session.messages); self.session.cancelled.set()
        with self.assertRaises(InterruptedError): self.session.ask('count rows')
        self.assertEqual(len(self.session.messages),before)
    def test_save_failure_preserves_conversation(self):
        from unittest.mock import patch
        previous=list(self.session.messages)
        with patch.object(self.session,'save',side_effect=OSError('disk full')):
            with self.assertRaises(OSError): self.session.ask('count rows')
        self.assertEqual(self.session.messages,previous)
    def test_corrupt_sidecar(self):
        self.session.path.write_text('{"version":1,"messages":[{"kind":"answer"}]}')
        with self.assertRaises(ValueError): Session(self.project)

    def test_answer_provenance_is_captured_before_query(self):
        other = self.session.paste('value\n9\n')
        self.session.table = 'pasted_data'
        original_query = self.project.query
        def switch_then_query(*args, **kwargs):
            self.session.table = other
            return original_query(*args, **kwargs)
        self.project.query = switch_then_query
        answer = self.session.ask('count rows')
        self.assertEqual(answer['source'], 'pasted_data')
        self.project.query = original_query

    def test_manual_sql_has_explicit_multi_table_provenance(self):
        self.session.paste('value\n9\n')
        answer = self.session.ask('SQL: SELECT count(*) FROM pasted_data')
        self.assertEqual(answer['source'], 'Imported tables referenced by manual SQL')

    def test_malformed_root_and_answer_metadata_are_clear_errors(self):
        for content in ('[]', '{"version":1,"table":[],"messages":[]}',
                        '{"version":1,"messages":[{"kind":"answer","question":"q","sql":"s","columns":[],"rows":[],"total":true,"chart":false,"source":null}]}'):
            self.session.path.write_text(content)
            with self.subTest(content=content), self.assertRaisesRegex(ValueError, 'conversation|selected table|answer'):
                Session(self.project)

    def test_import_card_save_failure_recovers_project_table(self):
        from unittest.mock import patch
        source = Path(self.tmp.name) / 'survives.csv'
        source.write_text('value\n3\n')
        previous = self.session.table
        with patch.object(self.session, 'save', side_effect=OSError('disk full')):
            with self.assertRaisesRegex(OSError, 'remains in the project'):
                self.session.import_file(source)
        self.assertEqual(self.session.table, previous)
        self.assertEqual(len(self.project.tables()), 2)
        reopened = Session(self.project)
        recovered = [m for m in reopened.messages if m['kind'] == 'file' and 'recovered import' in m['text']]
        self.assertEqual(len(recovered), 1)
        self.assertEqual(recovered[0]['table'], 'survives')

    def test_reopen_recovers_table_when_sidecar_was_never_created(self):
        other_path = Path(self.tmp.name) / 'fresh'
        other = Project.create(other_path)
        source = Path(self.tmp.name) / 'orphan.csv'
        source.write_text('value\n4\n')
        other.import_file(source)
        self.assertFalse((other_path / 'replica.json').exists())
        reopened = Session(other)
        self.assertEqual(reopened.messages, [{'kind':'file','text':'orphan.csv (recovered import)','table':'orphan'}])
        other.close()

if __name__=='__main__': unittest.main()
