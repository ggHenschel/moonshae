from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QInputDialog
from mainwindow import DistMainWindow
from controller import Controller
import json

class App(QApplication):
    def __init__(self, args):
        super().__init__(args)
        self.setApplicationName("Bully App")

    def run(self):
        try:
            with open("config.json") as config:

                data = json.loads(config.read())
                port = data["port"]
                service_id = data["service_id"]
        except:
            ok1 = False
            ok2 = False
            while not (ok1 and ok2):
                if not ok1:
                    port, ok1 = QInputDialog.getText(None, "Port Choice", "Port:")
                if not ok2:
                    service_id, ok2 = QInputDialog.getText(None, "ID Choice", "ID:")

        self.mw = DistMainWindow()
        self.cont = Controller(self.mw, port, service_id)
        self.mw.show()
