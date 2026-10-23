import os
os.environ['QT_QPA_PLATFORM']='offscreen'
import tempfile
import time
import unittest
from pathlib import Path
from PySide6.QtWidgets import QApplication, QTableView
from tables_replica.ui import Window, bar_geometry

app=QApplication.instance() or QApplication([])
class QtWorkflow(unittest.TestCase):
    def test_signed_chart_geometry_and_null_label_value(self):
        baseline, rects = bar_geometry([5.0, -5.0, None, 0.0], 440)
        self.assertEqual(baseline, 107.5)
        self.assertEqual(rects[0][1], 35)
        self.assertEqual(rects[1][1], int(baseline))
        self.assertIsNone(rects[2])
        self.assertEqual(rects[3][3], 0)
        positive_baseline, positive = bar_geometry([5.0, 2.5], 440)
        self.assertEqual(positive_baseline, 180)
        self.assertEqual(positive[0][1], 35)
        self.assertEqual(positive[1][1], 107)

    def test_card_controls_disabled_during_worker_and_select_save_failure_is_handled(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'project'; window=Window(); window.attach(path,True)
            first=window.session.paste('value\n1\n'); second=window.session.paste('value\n2\n')
            window.render()
            previous=window.session.table
            with patch.object(window.session,'save',side_effect=OSError('disk full')):
                window.select(first)
            self.assertEqual(window.session.table,previous)
            self.assertIn('Could not save selected table',window.status.text())
            window.busy(lambda:(time.sleep(.1), 'done')[1],lambda _:None)
            self.assertTrue(window.prompt.isReadOnly())
            self.assertTrue(window.card_controls)
            self.assertTrue(all(not button.isEnabled() for button in window.card_controls))
            window.select(first)
            self.assertEqual(window.session.table,previous)
            deadline=time.monotonic()+3
            while window.worker and time.monotonic()<deadline:
                app.processEvents(); time.sleep(.01)
            self.assertFalse(window.prompt.isReadOnly())
            self.assertTrue(all(button.isEnabled() for button in window.card_controls))
            window.close()

    def test_question_error_reopen_close(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'project'; window=Window(); window.attach(path,True)
            window.session.paste('region,amount\nNorth,555.75\nSouth,419.75\nWest,408.75\n')
            window.prompt.setPlainText('sum amount by region bar chart'); window.ask()
            deadline=time.monotonic()+5
            while window.worker and time.monotonic()<deadline:
                app.processEvents(); time.sleep(.01)
            self.assertIsNone(window.worker); self.assertEqual(len(window.findChildren(QTableView)),1)
            self.assertIn('1384.25',str(window.session.ask('sum amount')['rows']))
            previous=len(window.session.messages); window.prompt.setPlainText('unsupported'); window.ask()
            while window.worker and time.monotonic()<deadline:
                app.processEvents(); time.sleep(.01)
            self.assertEqual(len(window.session.messages),previous)
            self.assertIn('Supported:',window.status.text()); window.close()
            reopened=Window(); reopened.attach(path); self.assertEqual(len(reopened.session.messages),previous); reopened.close()
