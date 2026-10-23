"""Original neutral conversation UI grounded in observed workflow structure."""
import math
from pathlib import Path
from PySide6.QtCore import Qt, QThread, Signal, QAbstractTableModel, QModelIndex, QTimer
from PySide6.QtGui import QColor, QPainter, QAction, QKeySequence, QAccessible, QAccessibleAnnouncementEvent
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QPlainTextEdit, QScrollArea, QFileDialog, QDialog, QFrame,
    QDialogButtonBox, QTableView, QAbstractItemView, QMessageBox, QInputDialog)
from pip_tables.engine import Project
from .session import Session


class Worker(QThread):
    done = Signal(object, str)
    def __init__(self, operation):
        super().__init__(); self.operation = operation
    def run(self):
        try: self.done.emit(self.operation(), '')
        except Exception as e: self.done.emit(None, str(e))


class Bars(QWidget):
    def __init__(self, rows):
        super().__init__(); self.rows = rows[:50]; self.setMinimumHeight(230)
        self.setAccessibleName('Bar chart of first 50 result rows; exact values in artifact table below')
    def paintEvent(self, event):
        p = QPainter(self); p.fillRect(self.rect(), QColor('#fafafa'))
        values = []
        for row in self.rows:
            try:
                value = float(row[1])
                values.append(value if math.isfinite(value) else None)
            except (ValueError, TypeError): values.append(None)
        baseline, rects = bar_geometry(values, self.width())
        p.setPen(QColor('#777')); p.drawLine(20, int(baseline), self.width()-20, int(baseline))
        n = max(len(self.rows), 1); width = (self.width()-40)/n
        for i, (row, rect) in enumerate(zip(self.rows, rects)):
            if rect:
                x,y,w,h = rect
                p.fillRect(x,y,w,h,QColor(['#497da7','#639e97','#8c7aaf'][i%3]))
            if i % max(1, math.ceil(n / 6)) != 0:
                continue
            p.setPen(QColor('#202020'))
            p.drawText(int(25+i*width),200,str(row[0])[:16])
            label = ('NULL (not plotted)' if row[1] is None else
                     'Not finite (not plotted)' if rect is None else str(row[1])[:16])
            p.drawText(int(25+i*width),220,label)


def bar_geometry(values, canvas_width, chart_top=35, chart_height=145):
    """Return signed bars around zero; None values have no bar."""
    finite = [v for v in values if v is not None and math.isfinite(v)]
    positive = max([v for v in finite if v > 0] + [0])
    negative = abs(min([v for v in finite if v < 0] + [0]))
    scale = positive + negative or 1
    baseline = chart_top + chart_height * positive / scale
    slot = (canvas_width - 40) / max(len(values), 1)
    rects = []
    for i, value in enumerate(values):
        if value is None or not math.isfinite(value):
            rects.append(None); continue
        height = abs(value) / scale * chart_height
        y = baseline - height if value >= 0 else baseline
        rects.append((int(25 + i * slot), int(y), max(1, int(slot - 18)), max(0, int(height))))
    return baseline, rects


class ArtifactModel(QAbstractTableModel):
    """Lazy cells avoid allocating a widget item for every preview value."""
    def __init__(self, columns, rows, parent=None):
        super().__init__(parent); self.columns=columns; self.rows=rows
    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)
    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.columns)
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid(): return None
        value=self.rows[index.row()][index.column()]
        if role in (Qt.DisplayRole,Qt.ToolTipRole,Qt.AccessibleTextRole):
            return 'NULL' if value is None else str(value)
        if role==Qt.TextAlignmentRole and isinstance(value,(int,float)):
            return Qt.AlignRight | Qt.AlignVCenter
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role==Qt.DisplayRole:
            return self.columns[section] if orientation==Qt.Horizontal else str(section+1)


def grid(columns, rows):
    table=QTableView(); table.setModel(ArtifactModel(columns,rows,table))
    table.setAccessibleName('Result artifact exact values')
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.horizontalHeader().setStretchLastSection(True)
    table.setMinimumHeight(min(330,70+len(rows)*29)); return table


class Window(QMainWindow):
    def __init__(self):
        super().__init__(); self.session = None; self.worker = None; self.cancelled = False
        self.setWindowTitle('Tables Replica — Neutral Core'); self.resize(1120,800); self.setMinimumSize(900,720)
        outer = QWidget(); self.setCentralWidget(outer); root = QHBoxLayout(outer); root.setContentsMargins(0,0,0,0)
        rail = QWidget(); rail.setFixedWidth(80); nav = QVBoxLayout(rail)
        nav.addWidget(QLabel('TR'))
        self.controls=[]
        self.card_controls=[]
        for title, fn in [('New',self.new_project),('Open',self.open_project),('+ File',self.add_file),('+ CSV',self.paste_csv)]:
            b=QPushButton(title); b.clicked.connect(fn); nav.addWidget(b); self.controls.append(b)
        nav.addStretch(); nav.addWidget(QLabel('Local\nRules'))
        root.addWidget(rail); root.addStretch(1)
        conversation=QWidget();conversation.setMaximumWidth(920);main=QVBoxLayout(conversation)
        root.addWidget(conversation,10);root.addStretch(1)
        self.title=QLabel('A conversation with your data'); self.title.setTextFormat(Qt.PlainText); main.addWidget(self.title)
        self.scroll=QScrollArea(); self.scroll.setWidgetResizable(True); main.addWidget(self.scroll,1)
        self.feed=QWidget(); self.messages=QVBoxLayout(self.feed); self.messages.setContentsMargins(40,20,40,20); self.scroll.setWidget(self.feed)
        self.status=QLabel('Create or open a project to begin.'); self.status.setTextFormat(Qt.PlainText); self.status.setAccessibleName('Operation status'); self.status.setWordWrap(True); main.addWidget(self.status)
        self.prompt=QPlainTextEdit(); self.prompt.setMaximumHeight(90); self.prompt.setPlaceholderText('sum amount by region bar chart'); self.prompt.setAccessibleName('Analysis question or SQL prefixed with SQL:'); main.addWidget(self.prompt)
        row=QHBoxLayout(); main.addLayout(row); row.addWidget(QLabel('Supported rules + manual SQL • exact columns required'))
        self.stop=QPushButton('Stop'); self.stop.setEnabled(False); self.stop.clicked.connect(self.cancel); row.addWidget(self.stop)
        self.send=QPushButton('Analyze'); self.send.setObjectName('analyze'); self.send.clicked.connect(self.ask); row.addWidget(self.send)
        self.setStyleSheet('QWidget { background:#191919; color:#eeeeee; font-size:13px; } QPushButton { background:#292929; border:1px solid #444; border-radius:6px; padding:8px; } QPushButton:focus { border:2px solid #819df3; } QPlainTextEdit,QTableWidget { background:#222; border:1px solid #444; border-radius:8px; } QPushButton:disabled { color:#777; background:#202020; border-color:#303030; } QPushButton#analyze { background:#365f9f; border-color:#365f9f; color:#fff; } QPushButton#analyze:disabled { background:#202020; color:#777; border-color:#303030; } QPushButton#analyze:focus { border:2px solid #b7cbff; } QFrame#artifact { border:1px solid #444; border-radius:8px; } QLabel { padding:6px; } QHeaderView::section { background:#292929; color:#bbb; padding:6px; }')
        file_menu=self.menuBar().addMenu('File')
        for title,shortcut,handler in [('New project','Ctrl+N',self.new_project),('Open project','Ctrl+O',self.open_project),('Add file','Ctrl+I',self.add_file),('Analyze','Ctrl+Return',self.ask)]:
            action=QAction(title,self);action.setShortcut(QKeySequence(shortcut));action.triggered.connect(handler)
            file_menu.addAction(action);self.controls.append(action)
        quit_action=file_menu.addAction('Quit',self.close);quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.setMenuRole(QAction.MenuRole.QuitRole)
        about=self.menuBar().addMenu('Help').addAction('About',self.about)
        about.setMenuRole(QAction.MenuRole.AboutRole)
        self.render()

    def about(self):
        dialog=QMessageBox(self);dialog.setWindowTitle('About Tables Replica')
        dialog.setTextFormat(Qt.PlainText)
        dialog.setText('Tables Replica 0.1.0-alpha.1\nOriginal local conversation workflow prototype.\n\nMaintainer: Ghostzy0\nSource: github.com/Ghostzy0/pip-tables-replica\nShared engine: github.com/Ghostzy0/pip-tables\n\nObserved Julius workflow/layout reference; no affiliation, vendor assets or arbitrary AI. Supported rules and manual SQL only.\n\nMIT application; dynamic Qt/PySide LGPLv3, DuckDB/openpyxl MIT. See bundled notices. Projects are plaintext on this Mac; no account/server/provider. Experimental ad-hoc signed, not notarised.')
        dialog.exec()

    def set_status(self, text):
        self.status.setText(text);self.status.setAccessibleName(text)
        QAccessible.updateAccessibility(QAccessibleAnnouncementEvent(self.status,text))

    def busy(self, operation, after):
        if self.worker: return
        self.cancelled=False
        if self.session: self.session.cancelled.clear()
        self.stop.setEnabled(True); self.send.setEnabled(False); self.prompt.setReadOnly(True)
        for b in self.controls: b.setEnabled(False)
        for b in self.card_controls: b.setEnabled(False)
        self.set_status('Working locally…')
        self.worker=Worker(operation)
        def finished(value,error):
            worker=self.worker; worker.wait(); self.worker=None
            self.stop.setEnabled(False); self.send.setEnabled(True); self.prompt.setReadOnly(False)
            for b in self.controls: b.setEnabled(True)
            for b in self.card_controls: b.setEnabled(True)
            self.set_status(error or ('Stop requested. Completed work may remain saved in this project.' if self.cancelled else 'Ready • local result'))
            if not error: after(value)
        self.worker.done.connect(finished); self.worker.start()

    def cancel(self):
        self.cancelled=True
        if self.session:
            self.session.cancelled.set()
            self.session.project.cancel()
        self.set_status('Stopping current operation…')

    def attach(self,path,create=False):
        candidate = Project.create(path) if create else Project(path)
        try: session=Session(candidate)
        except Exception:
            candidate.close(); raise
        if self.session: self.session.project.close()
        self.session=session; self.title.setText(Path(path).name+' — local conversation'); self.render(); self.set_status('Project open. Add data, select a file card or ask a supported question.'); self.prompt.setFocus()
    def new_project(self):
        path=QFileDialog.getExistingDirectory(self,'Choose empty project folder')
        if path:
            try: self.attach(path,True)
            except Exception as e: self.set_status(str(e))
    def open_project(self):
        path=QFileDialog.getExistingDirectory(self,'Open project folder')
        if path:
            try: self.attach(path)
            except Exception as e: self.set_status(str(e))
    def add_file(self):
        if not self.session: self.set_status('Create or open a project first'); return
        path,_=QFileDialog.getOpenFileName(self,'Add selected data file','','Data (*.csv *.xlsx *.json *.ndjson *.parquet)')
        if path: self.busy(lambda:self.session.import_file(path),lambda _:self.render())
    def paste_csv(self):
        if not self.session: self.set_status('Create or open a project first'); return
        text,ok=QInputDialog.getMultiLineText(self,'Paste CSV','Header row followed by data (up to 2 MB)')
        if ok: self.busy(lambda:self.session.paste(text),lambda _:self.render())
    def ask(self):
        if not self.session: self.set_status('Create or open a project first'); return
        text=self.prompt.toPlainText().strip()
        if text: self.busy(lambda:self.session.ask(text),lambda _:(self.prompt.clear(),self.render()))
    def render(self):
        self.card_controls = []
        while self.messages.count():
            item=self.messages.takeAt(0)
            if item.widget():
                item.widget().hide(); item.widget().deleteLater()
        if not self.session or not self.session.messages:
            label=QLabel('Add a file or paste CSV, then ask a supported question.\n\nTry: count rows · sum amount · nulls amount\nsum amount by region bar chart\nSQL: SELECT …\n\nThis partial replica uses deterministic rules, not arbitrary AI analysis.'); label.setWordWrap(True); self.messages.addWidget(label)
        for message in self.session.messages if self.session else []:
            if message['kind']=='file':
                label=QLabel('FILE  '+message['text']+'\nImported table: '+message['table']); label.setWordWrap(True); label.setTextFormat(Qt.PlainText); self.messages.addWidget(label)
                b=QPushButton('Use this file / preview'); b.clicked.connect(lambda checked=False,t=message['table']:self.select(t)); self.messages.addWidget(b); self.card_controls.append(b)
            else:
                q=QLabel('YOU\n'+message['question']); q.setWordWrap(True); q.setTextFormat(Qt.PlainText); self.messages.addWidget(q)
                label=QLabel('LOCAL RULE / SQL RESULT\nSource: '+str(message['source'])+' • '+str(message['total'])+' result rows\n'+message['sql']); label.setWordWrap(True); label.setTextFormat(Qt.PlainText); self.messages.addWidget(label)
                if message['chart']:
                    self.messages.addWidget(QLabel('Bar chart · first 50 result rows · NULL/nonfinite values are not plotted'))
                    self.messages.addWidget(Bars(message['rows']))
                card=QFrame();card.setObjectName('artifact');body=QVBoxLayout(card);header=QHBoxLayout()
                header.addWidget(QLabel('analysis.csv · preview up to 1,000 rows'),1)
                export=QPushButton('View / Export CSV'); export.setAccessibleName('View or export CSV result artifact')
                export.clicked.connect(lambda checked=False,m=message:self.export_dialog(m));header.addWidget(export)
                body.addLayout(header);body.addWidget(grid(message['columns'],message['rows']));self.messages.addWidget(card)
                self.card_controls.append(export)
        self.messages.addStretch()
        if self.worker:
            for button in self.card_controls: button.setEnabled(False)
        QTimer.singleShot(0, lambda: self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum()))
    def select(self,table):
        if self.worker or not self.session: return
        previous = self.session.table
        self.session.table=table
        try:
            self.session.save()
        except Exception as exc:
            self.session.table=previous
            self.set_status(f'Could not save selected table: {exc}')
            return
        self.prompt.setPlainText('preview'); self.ask()
    def export_dialog(self,message):
        if self.worker: return
        dialog=QDialog(self); dialog.setWindowTitle('Export artifact'); layout=QVBoxLayout(dialog)
        layout.addWidget(QLabel('CSV preview • export reruns the displayed SQL against current project data'))
        layout.addWidget(grid(message['columns'],message['rows'][:20])); buttons=QDialogButtonBox(QDialogButtonBox.Cancel); download=buttons.addButton('Save CSV…',QDialogButtonBox.AcceptRole); layout.addWidget(buttons); buttons.rejected.connect(dialog.reject)
        def save():
            path,_=QFileDialog.getSaveFileName(dialog,'Save CSV','analysis.csv','CSV (*.csv)')
            if path:
                dialog.accept(); self.busy(lambda:self.session.project.export(message['sql'],path,'csv'),lambda _:None)
        download.clicked.connect(save); dialog.resize(700,450); dialog.exec()
    def closeEvent(self,event):
        if self.worker:
            self.cancel(); event.ignore(); self.set_status('Stopping. Close again when work finishes.'); return
        if self.session: self.session.project.close()
        event.accept()


def main():
    app=QApplication([]); app.setOrganizationName('Ghostzy0'); app.setApplicationName('io.github.ghostzy0.tables-replica'); app.setApplicationDisplayName('Tables Replica')
    window=Window(); window.show(); return app.exec()
