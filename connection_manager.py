from PyQt5.QtCore import QObject, pyqtSignal, qDebug
from PyQt5.QtNetwork import QUdpSocket, QHostAddress, QNetworkInterface
import json
import pickle
import time

#defines
ENTER_GROUP = "1"
LEADER_ALIVE = "4"
class ConnectionManager(QObject):

    signal_senda_data_to_message_manager = pyqtSignal(str)
    signal_leader_id = pyqtSignal(str)

    def __init__(self,port,service_id):
        self.multicastgroup = QHostAddress("224.0.1.232")
        self.mcast_port = 55421
        self.port = port
        super().__init__()
        self.udpSocket = QUdpSocket(self)
        self.udpSocket.bind(QHostAddress.AnyIPv4,int(port))
        self.udpSocket_multi = QUdpSocket(self)
        self.udpSocket_multi.bind(QHostAddress.AnyIPv4, self.mcast_port, QUdpSocket.ReuseAddressHint)
        self.udpSocket_multi.joinMulticastGroup(self.multicastgroup)
        self.udpSocket.readyRead.connect(self.processPendingDatagrams)
        self.udpSocket_multi.readyRead.connect(self.processPendingDatagrams_multi)

    def processPendingDatagrams(self):
        while self.udpSocket.hasPendingDatagrams():
            datagram, host, port = self.udpSocket.readDatagram(self.udpSocket.pendingDatagramSize())
            self.message_received(datagram,host,port)

    def processPendingDatagrams_multi(self):
        while self.udpSocket_multi.hasPendingDatagrams():
            datagram, host, port = self.udpSocket_multi.readDatagram(self.udpSocket_multi.pendingDatagramSize())
            self.message_received(datagram,host,port)

    def message_received(self,datagram,host, port):
        code, msg = pickle.loads(datagram)
        data = {"code":str(code),"msg":str(msg),"host":str(host.toString()),"port":str(port)}
        jdata = json.dumps(data)
        self.signal_senda_data_to_message_manager.emit(jdata)

    def send_message(self,jdata,ip,port=0):
        if port == 0:
            port = self.port
        data = json.loads(jdata)
        self.udpSocket.writeDatagram(pickle.dumps((data["code"],data["msg"])),QHostAddress(ip),int(port))

    def send_multicast_message(self,jdata):
        data = json.loads(jdata)
        self.udpSocket_multi.writeDatagram(pickle.dumps((data["code"],data["msg"])),self.multicastgroup,self.mcast_port)

    def alive(self, addr, port):
        data = {"code":LEADER_ALIVE,"msg":"Heart", "ip":addr, "port":port}
        jdata = json.dumps(data)
        self.send_message(jdata,addr,port)

    def get_ip(self):
        index_Interface = self.udpSocket_multi.multicastInterface()
        interface_Network = QNetworkInterface.interfaceFromIndex(index_Interface.index())
        own_addr = interface_Network.allAddresses()[0].toString()

        return own_addr
