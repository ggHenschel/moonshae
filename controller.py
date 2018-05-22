from PyQt5.QtCore import pyqtSlot, QObject, QThread, pyqtSignal, QDateTime, qDebug
from PyQt5.QtWidgets import QApplication
from message_manager import MessageManager
from connection_manager import ConnectionManager
from election_handler import ElectionHandler
import json
import time
import threading as th

ENTER_GROUP = "1"
ELECTION = "2"
NEW_LEADER = "3"

class AliveChecker(QThread):
    signal_election_is_due = pyqtSignal()

    def __init__(self,controller,leader_ip,leader_port, connection_manager, alive_timer=2):
        super().__init__()
        self.leader_ip = leader_ip
        self.leader_port = leader_port
        self.alive_timer = alive_timer
        self.connection_manager = connection_manager
        self.leader_alive = True

    def run(self):
        while self.leader_alive:
            self.leader_alive = False
            self.connection_manager.alive(self.leader_ip,self.leader_port)
            time.sleep(self.alive_timer)
        self.signal_election_is_due.emit()

    def set_leader(self,leader_ip,leader_port):
        self.leader_ip = leader_ip
        self.leader_port = leader_port
        self.leader_alive = True

    def set_alive(self):
        self.leader_alive = True

class Controller(QObject):

    def __init__(self,main_window,port,service_id):
        super().__init__()
        self.main_window = main_window
        #ConnectionManager (create Slots)
        self.connection_manager = ConnectionManager(port,service_id)
        self.message_manager = MessageManager(self.connection_manager, service_id)
        self.message_manager.signal_message_received.connect(self.print_string)
        self.message_manager.signal_election_responded.connect(self.set_election)
        self.message_manager.signal_leader_responded.connect(self.leader_has_been_found)
        self.message_manager.signal_has_message_to_send.connect(self.send_udp_message)
        self.message_manager.signal_leader_alive.connect(self.set_alive)

        data = {"port":str(port),"leader":"Null"}
        jdata = json.dumps(data)
        self.main_window.set_details(jdata)
        self.main_window.signal_has_message_to_send.connect(self.send_udp_message)
        self.main_window.signal_has_multicast_to_send.connect(self.send_multicast_message)
        self.main_window.signal_start_checking.connect(self.close)

        self.own_port = port
        self.service_id = service_id
        self.leader_ip = None
        self.leader_port = 0
        self.leader_id = " "
        self.election = True
        self.leader_alive = False
        self.iam_leader = False

        self.control_boolean = False
        self.alive_checker_thread = AliveChecker(self,self.leader_ip,self.leader_port,self.connection_manager)
        self.alive_checker_thread.signal_election_is_due.connect(self.do_election)

        #do first multicast
        self.th = th.Thread(target= self.request_group)
        self.th.start()



    def request_group(self):
        data = {"code": ENTER_GROUP, "msg": self.own_port}
        jdata = json.dumps(data)
        self.connection_manager.send_multicast_message(jdata)
        qDebug(QDateTime.currentDateTime().toString())
        time.sleep(2)
        qDebug(QDateTime.currentDateTime().toString())
        if self.leader_ip is None:
            self.iam_leader = True
            self.message_manager.set_is_leader(True)
            self.message_manager.send_message_to_main_window(str("I'm Leader!"))
        else:
            self.iam_leader = False
            self.message_manager.set_is_leader(False)


    @pyqtSlot(str)
    def print_string(self,string):
        self.main_window.print_string(string)

    @pyqtSlot(str)
    def send_udp_message(self,jdata):
        self.connection_manager.send_message(jdata)

    @pyqtSlot(str)
    def send_multicast_message(self,jdata):
        self.connection_manager.send_multicast_message(jdata)

    def do_election(self):
        election_handler = ElectionHandler(self.service_id, self.message_manager)
        self.leader_ip, self.leader_port, self.leader_id = election_handler.do_election()
        election_handler.deleteLater()
        self.leader_alive = True
        self.alive_checker_thread.set_leader(self.leader_ip, self.leader_port)
        self.alive_checker_thread.start()

    def elected(self):
        self.message_manager.send_message_to_main_window("elected")
        data = {"code": NEW_LEADER, "msg": self.service_id}
        jdata = json.dumps(data)
        self.connection_manager.send_multicast_message(jdata)

    @pyqtSlot(bool)
    def set_election(self, status):
        self.election = status


    def set_is_leader(self):
        self.message_manager.send_message_to_main_window(str("id leader " + self.leader[0]))
        if self.leader[0] != " ":
            if int(self.leader[0]) == int(self.service_id):
                return True

        return False

    @pyqtSlot()
    def set_alive(self):
        self.alive_checker_thread.set_alive()

    @pyqtSlot(str,str,str)
    def leader_has_been_found(self,id,ip,port):
        self.leader_ip = ip
        self.leader_port = port
        self.leader_id = id
        self.leader_alive = True
        self.alive_checker_thread.set_leader(self.leader_ip,self.leader_port)
        self.alive_checker_thread.start()

    @pyqtSlot()
    def close(self):
        self.alive_checker_thread.terminate()


    # OLD CODE - DELETE AFTER
    # def check_leader(self):
    #     self.control_boolean = True
    #     while self.control_boolean:
    #         sleep_time = 4
    #         self.message_manager.set_is_leader(self.set_is_leader())
    #         if self.leader[0] == " ":#check if exists leader
    #             data = {"code":ENTER_GROUP, "msg":self.own_port}
    #             jdata = json.dumps(data)
    #             self.connection_manager.send_multicast_message(jdata)
    #             #set leader as self
    #             self.leader = (self.service_id, self.connection_manager.get_ip(), self.own_port)
    #             data = {"port": self.own_port, "leader": self.service_id}
    #             jdata = json.dumps(data)
    #             self.main_window.set_details(jdata)
    #             self.message_manager.send_message_to_main_window("Enter new member")
    #         elif self.leader[0] == self.service_id:#check if it is the leader
    #             sleep_time = 10
    #         elif not self.leader_alive and self.election:
    #             election_handler = ElectionHandler(self.service_id,self.message_manager)
    #             self.leader = election_handler.do_election()
    #             election_handler.deleteLater()
    #         else:
    #             self.leader_alive = False
    #             self.connection_manager.alive(self.leader[1], self.leader[2], self.own_port)
    #
    #         time.sleep(sleep_time)
