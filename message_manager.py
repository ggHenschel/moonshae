from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, qDebug
import json
import pickle
import threading as th

ENTER_GROUP = "1"
ELECTION = "2"
NEW_LEADER = "3"
LEADER_ALIVE = "4"
ELECTION_STOP = "5"
MESSAGE = "42"

class MessageManager(QObject):

    signal_message_received = pyqtSignal(str, name='Message')
    signal_election_responded = pyqtSignal(bool)
    signal_leader_responded = pyqtSignal(str, str, str)
    signal_leader_alive = pyqtSignal()
    signal_has_message_to_send = pyqtSignal(str)
    signal_candidate_found = pyqtSignal(str, str, str, bool)

    def __init__(self,connection_manager, service_id):
        super().__init__()
        self.connect_manager = connection_manager
        self.connect_manager.signal_senda_data_to_message_manager.connect(self.process_message)
        self.is_leader = False
        self.service_id = service_id
        self.election_happening = False
        self.ip = self.connect_manager.get_ip

    def send_message_to_main_window(self,string):
        self.signal_message_received.emit(string)

    @pyqtSlot(str)
    def process_message(self,jdata):
        data = json.loads(jdata)
        if data["code"] == ENTER_GROUP:
            if self.is_leader and not self.ip==data["host"]:
                ndata = {"code": NEW_LEADER, "msg": self.service_id}
                jdata = json.dumps(ndata)
                self.connect_manager.send_message(jdata,data["host"],data["msg"])
                self.send_message_to_main_window("Info sended to new member:"+data["host"]+":"+data["msg"])
        elif data["code"] == ELECTION and self.election_happening:
            if int(data["msg"]) > self.leader_id:
                self.signal_candidate_found.emit(data["msg"],data["host"],data["port"],False)
        elif data["code"] == NEW_LEADER:
            self.signal_leader_responded.emit(data["msg"], data["host"], data["port"])
            self.send_message_to_main_window("New leader is: " + str(data["msg"]))
        elif data["code"] == LEADER_ALIVE:
            if self.is_leader:
                ndata = {"code": LEADER_ALIVE, "msg": self.service_id, "ip": data["host"], "port": data["msg"]}
                jdata = json.dumps(ndata)
                self.connect_manager.send_message(jdata,data["host"],data["msg"])
            else:
                self.signal_leader_alive.emit(True)
        elif data["code"] == ELECTION_STOP:
            if self.election_happening:
                self.signal_candidate_found.emit(data["msg"], data["host"], data["port"], True)
                self.election_finished()
            else:
                qDebug("Late Election")
        else:
            self.send_message_to_main_window("Unknown Code")

    def set_as_leader(self,id):
        self.is_leader = True
        data = {"code":ELECTION_STOP,"msg":id}
        jdata = json.dumps(data)
        self.connect_manager.send_multicast_message(jdata)


    def election_start(self,id):
        self.election_happening = True
        self.post_election(id)

    def election_finished(self):
        self.election_happening = False

    def post_election(self,id):
        data = {"code":ELECTION,"msg":str(id)}
        jdata = json.dumps(data)
        self.connect_manager.send_multicast_message(jdata)

    def set_is_leader(self,is_leader):
        self.is_leader = is_leader
