from PyQt5.QtCore import QThread, QObject, QSemaphore, pyqtSignal,qDebug, pyqtSlot
from random import uniform
from time import sleep

class NonCriticalWorker(QThread):

    signal_non_critical_part_done = pyqtSignal()


    def run(self):
        i = uniform(2.0,16.0)
        #avisa o sleeptime
        qDebug("NCW em "+str(i)+"s sleep")
        sleep(i)
        qDebug("NCW acordou")
        #avisa que terminou
        self.signal_non_critical_part_done.emit()

class CriticalWorker(QThread):
    signal_critical_part_done = pyqtSignal()

    def run(self):
        i = uniform(2.0, 4.0)
        # avisa o sleeptime
        qDebug("CW em " + str(i) + "s sleep")
        sleep(i)
        qDebug("CW acordou")
        # avisa que terminou
        self.signal_critical_part_done.emit()

class WorkerController(QObject):

    signal_request_critical = pyqtSlot(int)
    signal_send_free_message = pyqtSignal(int, str)

    def __init__(self,total_number_of_process):
        super().__init__()
        #self.semaphore = QSemaphore(1)
        self.non_critical_worker = NonCriticalWorker()
        self.critical_worker = CriticalWorker()
        self.total_number_of_process = total_number_of_process
        self.total_number_of_oks = 0
        self.list_of_priority = []
        self.tick = 0
        self.in_critical = False
        self.non_critical_worker.signal_non_critical_part_done.connect(self.non_critical_worker_done)
        self.critical_worker.signal_critical_part_done.connect(self.critical_worker_done)

    def start(self):
        self.tick+=1
        self.non_critical_worker.start()

    def set_total_numeber_of_process(self,n):
        self.total_number_of_process = n

    def add_to_list(self,tick,ip):
        self.list_of_priority.append((ip,tick))
        self.list_of_priority.sort(key=lambda tup: tup[1])

    def process_list(self):
        for ip, tick in self.list_of_priority:
            self.signal_send_free_message.emit(ip,self.tick)

    def end(self):
        self.critical_worker.terminate()
        self.non_critical_worker.terminate()

    @pyqtSlot()
    def non_critical_worker_done(self):
        self.tick+=1
        self.signal_request_critical.emit(self.tick)
        self.in_critical = True

    @pyqtSlot()
    def critical_worker_done(self):
        self.tick+=1
        self.in_critical = False
        self.non_critical_worker.start()
        self.process_list()

    def receive_ok(self,tick):
        self.total_number_of_oks+=1
        if tick>self.tick:
            self.tick=tick+1
        else:
            self.tick+=1
        self.total_number_of_oks+=1
        qDebug("OK Receveid #"+self.total_number_of_oks+" of "+self.total_number_of_process)
        if self.total_number_of_oks == self.total_number_of_process:
            self.total_number_of_oks =0
            self.critical_worker.start()


    def receive_request(self,tick,ip):
        self.total_number_of_oks += 1
        if tick > self.tick:
            self.tick = tick + 1
        else:
            self.tick += 1
        self.add_to_list(tick,ip)
        if not self.in_critical:
            self.process_list()
