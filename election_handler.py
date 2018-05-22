from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, QSemaphore, QObject, qDebug
import time

ENTER_GROUP = "1"
ELECTION = "2"
NEW_LEADER = "3"

class ElectionHandler(QObject):

    signal_send_multicast_message = pyqtSignal(str)

    def __init__(self,self_id,message_manager,election_time=5):
        super().__init__()
        self.id = self_id
        self.message_manager = message_manager
        self.semaphore = QSemaphore(1)
        self.self_elected = True
        self.election_timer = election_time
        self.message_manager.signal_candidate_found.connect(self.candidate_found)

    def do_election(self):
        #Sinal Multicast START ELECTION
        self.message_manager.election_started(self.id)
        time.sleep(self.election_timer)
        if self.id == self.leader_id:
            self.message_manager.set_as_leader()
        #Esperar Eleição Acabar
        return self.leader_ip, self.leader_port, self.leader_id


    @pyqtSlot(str, str, str,bool)
    def candidate_found(self, id, ip, port, stop=False):
        if stop and id < self.leader_id:
            qDebug("Coup is Happening")
        elif id > self.leader_id:
            self.leader_ip = ip
            self.leader_port = port
            self.leader_id = id
            self.message_manager.send_message_to_main_window("Candidate "+ip+" has id "+id+", and is the Bully of The Block")
            if stop:
                self.message_manager.election_finishe()
        elif id == self.id:
            pass
        elif id < self.id:
            self.message_manager.post_election(self.id)
