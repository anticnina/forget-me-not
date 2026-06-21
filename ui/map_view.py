from __future__ import annotations
import json
import os
from pathlib import Path

from PyQt6.QtCore import QFile, QIODevice, QObject, QTimer, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineScript, QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)
from PyQt6.QtCore import Qt

import models.map_model as map_model
import models.pin as pin_model
from models.map_model import Map
from models.user import User

ASSETS_DIR = Path(__file__).parent.parent / "assets"
_MAP_HTML_FILE = ASSETS_DIR / "_map.html"


# ── Custom page: enables local-file security flags + JS console ──

class _MapPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line, source):
        print(f"[MAP JS {level.name}] {message}  (line {line})")


# ── JS↔Python bridge ─────────────────────────────────────────

class MapBridge(QObject):
    pin_requested = pyqtSignal(float, float)

    @pyqtSlot(float, float)
    def mapClicked(self, lat: float, lng: float):           # noqa: N802
        self.pin_requested.emit(lat, lng)


# ── Map HTML template ────────────────────────────────────────

def _build_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <link rel="stylesheet" href="leaflet/leaflet.css"/>
  <style>
    @font-face { font-family: 'Nunito'; font-weight: 400;
      src: url('../fonts/Nunito-Regular.ttf') format('truetype'); }
    @font-face { font-family: 'Nunito'; font-weight: 600;
      src: url('../fonts/Nunito-SemiBold.ttf') format('truetype'); }
    @font-face { font-family: 'Nunito'; font-weight: 700;
      src: url('../fonts/Nunito-Bold.ttf') format('truetype'); }
    @font-face { font-family: 'Nunito'; font-style: italic; font-weight: 400;
      src: url('../fonts/Nunito-RegularItalic.ttf') format('truetype'); }
    html, body, #map { height: 100%; margin: 0; padding: 0;
      font-family: 'Nunito', sans-serif; }
    .flower-marker { cursor: pointer; }
    #counter {
      position: absolute; bottom: 24px; right: 12px; z-index: 1000;
      background: rgba(192,221,240,0.96); backdrop-filter: blur(4px);
      padding: 7px 16px; border-radius: 20px;
      font-family: 'Nunito', 'Segoe UI', sans-serif; font-size: 14px; font-weight: bold;
      color: #0D2333; box-shadow: 0 2px 8px rgba(30,111,168,.25);
      pointer-events: none; border: 1px solid #85C1E9;
      display: flex; align-items: center; gap: 6px;
    }
    .leaflet-popup-content b { font-size: 15px; }
    .popup-img { max-width: 180px; max-height: 120px; margin-top: 6px;
                 border-radius: 6px; display: block; }
  </style>
</head>
<body>
  <div id="map"></div>
  <div id="counter">
    <span style="display:inline-block;filter:hue-rotate(234deg) saturate(0.74) brightness(0.93)">🌸</span>
    <span id="cnt">0 memories</span>
  </div>

  <script src="leaflet/leaflet.js"></script>
  <script>
    // qwebchannel.js is injected by Qt before this script runs
    var map = L.map('map').setView([48.8566, 2.3522], 4);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19
    }).addTo(map);

    var markers = {};

    function makeIcon() {
      return L.divIcon({
        html: '<span style="font-size:28px;line-height:1;display:block;filter:hue-rotate(234deg) saturate(0.74) brightness(0.93);text-shadow:0 1px 4px rgba(0,0,0,.35);cursor:pointer">🌸</span>',
        className: '',
        iconSize: [32, 32], iconAnchor: [16, 16], popupAnchor: [0, -18]
      });
    }

    function _esc(s) {
      return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;')
                      .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }

    function loadPins(pinsJson) {
      var incoming = {};
      pinsJson.forEach(function(p){ incoming[p.id] = true; });
      Object.keys(markers).forEach(function(id){
        if (!incoming[id]) { map.removeLayer(markers[id]); delete markers[id]; }
      });
      pinsJson.forEach(function(p) {
        if (!markers[p.id]) {
          var m = L.marker([p.lat, p.lng], {icon: makeIcon()}).addTo(map);
          var html = '<b>' + _esc(p.name) + '</b>';
          if (p.desc) html += '<br/><span style="font-size:13px">' + _esc(p.desc) + '</span>';
          if (p.img)  html += '<br/><img class="popup-img" src="' + _esc(p.img) + '"/>';
          m.bindPopup(html, {maxWidth:220});
          markers[p.id] = m;
        }
      });
      updateCounter();
    }

    function updateCounter() {
      var n = Object.keys(markers).length;
      document.getElementById('cnt').textContent =
        n + (n === 1 ? ' memory' : ' memories');
    }

    // Bridge is set up after qwebchannel.js injection
    if (typeof QWebChannel !== 'undefined') {
      new QWebChannel(qt.webChannelTransport, function(ch) {
        window.pyBridge = ch.objects.bridge;
      });
    }

    map.on('click', function(e) {
      if (window.pyBridge) {
        window.pyBridge.mapClicked(e.latlng.lat, e.latlng.lng);
      }
    });
  </script>
</body>
</html>"""


# ── Invite collaborator dialog ────────────────────────────────

class InviteDialog(QDialog):
    def __init__(self, map_obj: Map, current_user: User, friends: list[User], parent=None):
        super().__init__(parent)
        self.map_obj = map_obj
        self.current_user = current_user
        self.setWindowTitle("Manage Map Access")
        self.setFixedSize(320, 420)
        self._build_ui(friends)

    def _build_ui(self, friends: list[User]):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.addWidget(QLabel(f"<b>Map:</b> {self.map_obj.title}"))
        root.addSpacing(4)
        root.addWidget(QLabel("Check friends to give them access:"))
        root.addSpacing(8)

        current_collabs = {u.id for u in map_model.get_collaborators(self.map_obj.id)}
        self.friend_list = QListWidget()
        self.friend_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for f in friends:
            item = QListWidgetItem(f"👤 {f.username}  ({f.full_name})")
            item.setData(Qt.ItemDataRole.UserRole, f.id)
            if f.id in current_collabs:
                item.setSelected(True)
                item.setText(item.text() + "  ✅")
            self.friend_list.addItem(item)
        root.addWidget(self.friend_list)

        root.addSpacing(12)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._on_save)
        root.addWidget(save_btn)

        self.setStyleSheet("""
            QDialog { background:#EAF4FB; }
            QLabel  { color:#1B2631; font-size:13px; font-weight:bold; }
            QListWidget { border:1px solid #85C1E9; border-radius:6px;
                          background:white; color:#1B2631; }
            QListWidget::item { padding:6px 8px; color:#1B2631; }
            QListWidget::item:hover { background:#BED9F0; }
            QListWidget::item:selected { background:#7EC8E3; color:#0D2333; }
            QPushButton { background:#1E6FA8; color:white; border:none;
                          border-radius:8px; padding:8px; font-size:14px;
                          font-weight:bold; }
            QPushButton:hover { background:#155A8A; }
        """)

    def _on_save(self):
        selected_ids = {
            item.data(Qt.ItemDataRole.UserRole)
            for item in self.friend_list.selectedItems()
        }
        all_ids = {
            self.friend_list.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self.friend_list.count())
        }
        for fid in selected_ids:
            map_model.add_collaborator(self.map_obj.id, fid)
        for fid in all_ids - selected_ids:
            map_model.remove_collaborator(self.map_obj.id, fid)
        self.accept()


# ── Main map widget ───────────────────────────────────────────

class MapView(QWidget):
    map_changed = pyqtSignal()

    def __init__(self, current_user: User, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.current_map: Map | None = None
        self._friends_provider = None
        self._pending_focus: tuple | None = None  # (lat, lng, pin_id)
        self._build_ui()
        self._setup_channel()
        self._setup_timer()

    # ── Construction ─────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        bar = QWidget()
        bar.setFixedHeight(46)
        bar.setStyleSheet("background:#C0DDF0; border-bottom:2px solid #85C1E9;")
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(12, 0, 12, 0)

        self.title_label = QLabel("← Select a map from the sidebar")
        self.title_label.setStyleSheet("font-size:14px;font-weight:bold;color:#0D2333;")
        bar_layout.addWidget(self.title_label)
        bar_layout.addStretch()

        btn_style = (
            "QPushButton { border:1.5px solid #1E6FA8; border-radius:7px; "
            "padding:4px 10px; font-size:13px; font-weight:bold; "
            "background:white; color:#1E6FA8; }"
            "QPushButton:hover { background:#D4EAF7; }"
        )

        self.privacy_btn = QPushButton()
        self.privacy_btn.setFixedWidth(130)
        self.privacy_btn.setStyleSheet(btn_style)
        self.privacy_btn.clicked.connect(self._toggle_privacy)
        self.privacy_btn.hide()
        bar_layout.addWidget(self.privacy_btn)

        self.invite_btn = QPushButton("👥 Manage Access")
        self.invite_btn.setFixedWidth(130)
        self.invite_btn.setStyleSheet(btn_style)
        self.invite_btn.clicked.connect(self._invite_friends)
        self.invite_btn.hide()
        bar_layout.addWidget(self.invite_btn)

        root.addWidget(bar)

        self.web_view = QWebEngineView()
        root.addWidget(self.web_view)

    def _setup_channel(self):
        # Use the custom page so JS console messages print to terminal
        page = _MapPage(self.web_view)
        self.web_view.setPage(page)

        # ── Critical: allow a file:// page to load local files and remote tiles ──
        s = page.settings()
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls,   True)
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)

        # Bridge
        self.bridge = MapBridge()
        self.bridge.pin_requested.connect(self._on_map_clicked)
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        page.setWebChannel(self.channel)

        # Inject qwebchannel.js at document-creation time so it's always available
        f = QFile(":/qtwebchannel/qwebchannel.js")
        if f.open(QIODevice.OpenModeFlag.ReadOnly):
            src = bytes(f.readAll()).decode("utf-8")
            f.close()
            script = QWebEngineScript()
            script.setName("qwebchannel_api")
            script.setSourceCode(src)
            script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
            script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
            page.scripts().insert(script)

    def _setup_timer(self):
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(5000)
        self.refresh_timer.timeout.connect(self._refresh_pins)

    # ── Public API ────────────────────────────────────────────

    def set_friends_provider(self, fn):
        self._friends_provider = fn

    def load_map(self, m: Map, focus: tuple | None = None):
        """Load a map. Pass focus=(lat, lng, pin_id) to pan to a specific pin after load."""
        self.refresh_timer.stop()
        try:
            self.web_view.loadFinished.disconnect(self._on_load_finished)
        except TypeError:
            pass

        self.current_map = m
        self._pending_focus = focus
        self.title_label.setText(m.title)
        self._update_controls()

        # Write HTML to assets/_map.html so relative paths (leaflet/*) resolve correctly
        _MAP_HTML_FILE.write_text(_build_html(), encoding="utf-8")
        self.web_view.loadFinished.connect(self._on_load_finished)
        self.web_view.setUrl(QUrl.fromLocalFile(str(_MAP_HTML_FILE)))
        self.refresh_timer.start()

    def clear(self):
        self.refresh_timer.stop()
        try:
            self.web_view.loadFinished.disconnect(self._on_load_finished)
        except TypeError:
            pass
        self.current_map = None
        self.title_label.setText("← Select a map from the sidebar")
        self.web_view.setHtml("")
        self.privacy_btn.hide()
        self.invite_btn.hide()

    # ── Internal ──────────────────────────────────────────────

    def _update_controls(self):
        if not self.current_map:
            return
        is_owner = map_model.is_owner(self.current_user.id, self.current_map)
        self.privacy_btn.setText(
            "🔒 Make Public" if self.current_map.is_private else "🌐 Make Private"
        )
        self.privacy_btn.setVisible(is_owner)
        self.invite_btn.setVisible(is_owner and self.current_map.is_private)

    def _on_load_finished(self, ok: bool):
        if ok:
            self._refresh_pins()
            if self._pending_focus:
                lat, lng, pin_id = self._pending_focus
                self._pending_focus = None
                QTimer.singleShot(700, lambda: self.focus_pin(lat, lng, pin_id))

    def focus_pin(self, lat: float, lng: float, pin_id: int):
        """Pan the map to the given coordinates and open that pin's popup."""
        js = (
            f"map.setView([{lat}, {lng}], 15);"
            f"if (markers[{pin_id}]) {{ markers[{pin_id}].openPopup(); }}"
        )
        self.web_view.page().runJavaScript(js)

    def _refresh_pins(self):
        if not self.current_map:
            return
        pins = pin_model.get_pins_for_map(self.current_map.id)
        payload = []
        for p in pins:
            img_url = ""
            if p.image_path and os.path.exists(p.image_path):
                img_url = QUrl.fromLocalFile(p.image_path).toString()
            payload.append({
                "id": p.id,
                "lat": p.latitude,
                "lng": p.longitude,
                "name": p.person_name,
                "desc": p.description or "",
                "img": img_url,
            })
        self.web_view.page().runJavaScript(f"loadPins({json.dumps(payload)});")

    # ── Slots ─────────────────────────────────────────────────

    def _on_map_clicked(self, lat: float, lng: float):
        if not self.current_map:
            return
        if not map_model.can_pin(self.current_user.id, self.current_map):
            QMessageBox.warning(self, "No access",
                                "You can view this map but only its owner and invited friends can add memories.")
            return
        from ui.pin_dialog import PinDialog
        dlg = PinDialog(lat, lng, self.current_map.id, self.current_user.id, self)
        if dlg.exec():
            self._refresh_pins()

    def _toggle_privacy(self):
        if not self.current_map:
            return
        map_model.update_privacy(self.current_map.id, not self.current_map.is_private)
        self.current_map = map_model.get_by_id(self.current_map.id)
        self._update_controls()
        self.map_changed.emit()

    def _invite_friends(self):
        if not self.current_map:
            return
        friends = self._friends_provider() if self._friends_provider else []
        if not friends:
            QMessageBox.information(self, "No friends yet",
                                    "Accept friend requests first, then manage map access.")
            return
        dlg = InviteDialog(self.current_map, self.current_user, friends, self)
        dlg.exec()
