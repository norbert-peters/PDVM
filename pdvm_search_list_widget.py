# pdvm_search_list_widget.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QLineEdit,
    QLabel, QSpinBox, QHeaderView, QGroupBox,
    QToolBar, QAction, QStyle, QComboBox, QSizePolicy, QScrollArea
)
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, pyqtSignal, QSize, QTimer
from datetime import datetime
from functools import partial
import logging

logger = logging.getLogger(__name__)

class PdvmTableModel(QAbstractTableModel):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.columns = columns
        self.rows = []

    def update_data(self, rows: list, columns: list):
        self.beginResetModel()
        self.rows = rows
        self.columns = columns
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return len(self.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        row = self.rows[index.row()]
        col = self.columns[index.column()]
        val = row.get(col)
        if isinstance(val, datetime):
            return val.strftime('%d.%m.%Y')
        return val

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.columns[section]
        return super().headerData(section, orientation, role)

    def guid_for_row(self, row_idx):
        return self.rows[row_idx].get('GUID')

class PdvmSearchListWidget(QWidget):
    """
    Such- und Auswahlliste mit Filter, Sortierung, Paging
    und Datumsteilen als leere Textfelder in Mode 0.
    """
    selectionChanged = pyqtSignal(list)

    def __init__(self, view_manager, table_name, parent=None):
        super().__init__(parent)
        self.vm = view_manager
        self.table = table_name
        self.filters = {}
        self.sort = []
        self.page = 0
        self.page_size = 25
        self.total = 0
        self.column_widths_applied = False

        self._init_ui()
        self._reload()
        QTimer.singleShot(0, self._apply_column_widths)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5,5,5,5)
        layout.setSpacing(8)

        # — Filterzeile —
        fb = QGroupBox("Filter")
        fl = QHBoxLayout(fb)
        definition = self.vm.get_view_definition(self.table)
        self.columns = [c['name'] for c in definition['columns']]
        self.meta    = {c['name']: c for c in definition['columns']}

        for col in self.columns:
            m = self.meta[col]
            if not m.get('searchable', False):
                continue
            fl.addWidget(QLabel(f"{col}:"))
            ft = m.get('filterType', 'contains')
            if ft == 'dateRange' and self.vm.mode == 0:
                ft = 'dateParts'

            if ft == 'contains':
                le = QLineEdit()
                le.setPlaceholderText("enthält …")
                le.setClearButtonEnabled(True)
                le.textChanged.connect(partial(self._set_contains, col))
                fl.addWidget(le)

            elif ft == 'dropdown':
                cb = QComboBox()
                cb.addItem("-- alle --", None)
                for opt in self.vm.get_lookup_options(m.get('lookup', {})):
                    cb.addItem(str(opt), opt)
                cb.currentIndexChanged.connect(partial(self._set_dropdown, col, cb))
                fl.addWidget(cb)

            elif ft == 'dateParts':
                for suffix, ph, w in [
                    ('_tag', 'TT', 45),
                    ('_monat', 'MM', 45),
                    ('_jahr', 'JJJJ', 60),
                ]:
                    dp = QLineEdit()
                    dp.setPlaceholderText(ph)
                    dp.setClearButtonEnabled(True)
                    dp.setFixedWidth(w)
                    dp.textChanged.connect(partial(self._set_datepart, col, suffix))
                    fl.addWidget(dp)

            else:
                le = QLineEdit()
                le.setClearButtonEnabled(True)
                le.textChanged.connect(partial(self._set_contains, col))
                fl.addWidget(le)

        layout.addWidget(fb)

        # — Toolbar mit Paging —
        tb = QToolBar()
        size = self.style().pixelMetric(QStyle.PM_SmallIconSize)
        tb.setIconSize(QSize(size, size))
        prev = QAction(self.style().standardIcon(QStyle.SP_ArrowLeft), 'Prev', self)
        nxt  = QAction(self.style().standardIcon(QStyle.SP_ArrowRight), 'Next', self)
        prev.triggered.connect(self._prev_page)
        nxt.triggered.connect(self._next_page)
        tb.addAction(prev)
        tb.addWidget(QLabel(" Seite "))
        self.lbl_page = QLabel()
        tb.addWidget(self.lbl_page)
        tb.addAction(nxt)
        tb.addSeparator()
        tb.addWidget(QLabel(" Zeilen/Seite: "))
        sp = QSpinBox(value=self.page_size, minimum=1, maximum=500)
        sp.valueChanged.connect(self._set_page_size)
        tb.addWidget(sp)
        layout.addWidget(tb)

        # — ScrollArea für Tabelle —
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0,0,0,0)

        # TableView
        self.model = PdvmTableModel(self.columns)
        self.table_view = QTableView()
        self.table_view.setModel(self.model)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(True)
        hdr = self.table_view.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Interactive)
        hdr.sectionClicked.connect(self._on_header)
        vbox.addWidget(self.table_view)

        scroll.setWidget(container)
        layout.addWidget(scroll)
        self.setLayout(layout)

    def _set_contains(self, col, txt):
        if txt:
            self.filters[col] = {'type':'contains','value':txt}
        else:
            self.filters.pop(col, None)
        self.page = 0
        self._reload()

    def _set_dropdown(self, col, combo, idx):
        val = combo.currentData()
        if val is None:
            self.filters.pop(col, None)
        else:
            self.filters[col] = {'type':'dropdown','value':val}
        self.page = 0
        self._reload()

    def _set_datepart(self, col, suffix, txt):
        key = col + suffix
        if txt:
            self.filters[key] = {'type':'contains','value':txt}
        else:
            self.filters.pop(key, None)
        self.page = 0
        self._reload()

    def _set_page_size(self, v):
        self.page_size = v
        self.page = 0
        self._reload()

    def _prev_page(self):
        if self.page > 0:
            self.page -= 1
            self._reload()

    def _next_page(self):
        if (self.page+1)*self.page_size < self.total:
            self.page += 1
            self._reload()

    def _on_header(self, idx):
        col = self.columns[idx]
        cur = next((s for s in self.sort if s[0]==col), None)
        direction = 'asc' if not cur or cur[1]=='desc' else 'desc'
        self.sort = [(col, direction)]
        self._reload()

    def _reload(self):
        rows, self.total = self.vm.query_view(
            table=self.table,
            filters=self.filters,
            sort=self.sort,
            page=self.page,
            page_size=self.page_size
        )
        for r in rows:
            for c, m in self.meta.items():
                if m.get('type') == 'date' and r.get(c) is not None:
                    r[c] = self.vm.pdvm_to_date(float(r[c]))
                if m.get('type') == 'lookup' and r.get(c) is not None:
                    r[c] = self.vm.get_lookup_display_value(m['lookup'], r[c])
        self.model.update_data(rows, self.columns)
        pages = (self.total + self.page_size - 1) // self.page_size
        self.lbl_page.setText(f"{self.page+1}/{pages}")
        if not self.column_widths_applied:
            self._apply_column_widths()
            self.column_widths_applied = True

    def _apply_column_widths(self):
        raw_fields = self.vm.metadata[self.table]['felder']
        pct_list = []
        for name in self.columns:
            fld = next((f for f in raw_fields if f.get("name",f.get("feld"))==name), {})
            raw = fld.get("ui",{}).get("width","0%")
            try:
                pct = int(str(raw).rstrip("%"))
            except:
                pct = 0
            pct_list.append(pct)
        total_pct = sum(pct_list) or 1
        dw = str(self.vm.display_width).rstrip("%")
        try:
            dw_val = int(dw)
        except:
            dw_val = 100
        parent_w = self.parent().width() if self.parent() else self.width()
        full_w = round(parent_w * (dw_val / 100.0))
        self.table_view.setFixedWidth(full_w + 20)
        for idx, pct in enumerate(pct_list):
            w = round(full_w * (pct / total_pct))
            self.table_view.setColumnWidth(idx, w)

    def emit_selection(self):
        sel = self.table_view.selectionModel().selectedRows()
        guids = [self.model.guid_for_row(idx.row()) for idx in sel]
        self.selectionChanged.emit(guids)

    def set_selected_guid(self, guid):
        # Wähle die Zeile mit passender GUID aus
        for row_idx, row in enumerate(self.model.rows):
            if row.get('GUID') == guid:
                sel_model = self.table_view.selectionModel()
                index = self.model.index(row_idx, 0)
                sel_model.select(index, sel_model.Select | sel_model.Rows)
                self.table_view.scrollTo(index)
                # Signal auslösen, damit selected_guid im Dialog gesetzt wird
                self.emit_selection()
                break
