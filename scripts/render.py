"""Synthetic offscreen source render, distinct from native/package evidence."""
import os
os.environ['QT_QPA_PLATFORM']='offscreen'
import sys,tempfile,json
from pathlib import Path
from PySide6.QtWidgets import QApplication
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pip_tables.engine import Project
from tables_replica.session import Session
from tables_replica.ui import Window
root=Path(__file__).resolve().parents[1];out=root/'.local-evidence/renders';out.mkdir(exist_ok=True)
app=QApplication([])
with tempfile.TemporaryDirectory() as temp:
 p=Project.create(Path(temp)/'Sample regional sales');s=Session(p);s.import_file(root/'examples/orders.csv');s.ask('sum amount by region bar chart');p.close()
 w=Window();w.attach(Path(temp)/'Sample regional sales');w.show()
 for width,height in [(1120,900),(900,720)]:
  w.resize(width,height);app.processEvents();app.processEvents();w.scroll.verticalScrollBar().setValue(w.scroll.verticalScrollBar().maximum());app.processEvents();w.grab().save(str(out/f'replica-{width}x{height}.png'))
 w.close()
print(out)
