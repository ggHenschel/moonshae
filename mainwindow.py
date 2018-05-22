from PyQt5.QtWidgets import QMainWindow, QDesktopWidget, QPushButton, QLabel, QInputDialog
from PyQt5 import uic
from PyQt5.QtCore import QObject, pyqtSignal
import json

MESSSAGE_CODE = "42"

class DistMainWindow(QMainWindow):

    signal_has_message_to_send = pyqtSignal(str)
    signal_has_multicast_to_send = pyqtSignal(str)
    signal_start_checking = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_UI()
        self.running = False

    def init_UI(self):
        self.ui = uic.loadUi("mainwindow.ui",self)
        self.setWindowTitle('Bully App')
        self.ui.m_closeButton.clicked.connect(self.on_close_clicked)
        self.ui.m_sendMessage.clicked.connect(self.on_send_message_clicked)
        self.ui.m_multicastButton.clicked.connect(self.on_multicast_message_clicked)

    def on_close_clicked(self):
        self.signal_start_checking.emit()
        self.close()

    def print_string(self,string):
        text = self.ui.m_textBrowser.toPlainText()
        text+="\n"+string
        self.ui.m_textBrowser.setText(text)

    def set_details(self,jdata):
        data = json.loads(jdata)
        self.ui.m_portLabel.setText(data["port"])
        self.ui.m_leaderDetais.setText(data["leader"])

    def on_send_message_clicked(self):
        ok1 = False
        ok2 = False
        while not (ok1 and ok2):
            if not ok1:
                ip, ok1 = QInputDialog.getText(None, "IP", "IP:")
            if not ok2:
                port, ok2 = QInputDialog.getText(None, "Port", "Port:")
            if not ok1 and not ok2:
                return
        msg, ok = QInputDialog.getMultiLineText(None,"Message","Type your Message:")
        if ok:
            data = {"ip":ip,"port":port,"msg":msg,"code":MESSSAGE_CODE}
            jdata = json.dumps(data)
            self.signal_has_message_to_send.emit(jdata)

    def on_multicast_message_clicked(self):
        msg, ok = QInputDialog.getMultiLineText(None, "Message", "Type your Message:")
        if ok:
            data = {"msg": msg, "code": MESSSAGE_CODE}
            jdata = json.dumps(data)
            self.signal_has_multicast_to_send.emit(jdata)
