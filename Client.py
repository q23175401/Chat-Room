from socket import *
import threading
import sys
import MainWindow
import time
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import QtGui


class MainWindow(QMainWindow, MainWindow.Ui_MainWindow):
    def __init__(self, name, port):
        super(self.__class__, self).__init__()
        self.setupUi(self)
        self.serverName = name
        self.serverPort = port
        self.socket = None
        self.thread = None
        self.errorMessage.setHidden(True)
        self.ZONE = 'N'
        self.P2connection = False
        self.SEX = "B"
        self.P2SEX = "B"

    def boyClicked(self):  # 男按鈕
        self.SEX = 'B'
        self.connectButton.setEnabled(True)
        self.setChoosenIcon('B')
        self.genderlabel.setText('性別:男')
        self.genderPicUser.setPixmap(QtGui.QPixmap(":/newPrefix/boy.png"))
        print("boy clicked")

    def girlClicked(self):  # 女按鈕
        self.SEX = 'G'
        self.connectButton.setEnabled(True)
        self.setChoosenIcon('G')
        self.genderlabel.setText('性別:女')
        self.genderPicUser.setPixmap(QtGui.QPixmap(":/newPrefix/girl.png"))
        print("girl clicked")

    def setChoosenIcon(self, gender):  # 改變選擇後的圖示
        if gender == 'B':  # 把男圈起來女的圈取消
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/newPrefix/boy_icon_choosen.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.boyButton.setIcon(icon)
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/newPrefix/girl_icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.girlButton.setIcon(icon)
        else:  # 把女圈起來男的圈取消
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/newPrefix/boy_icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.boyButton.setIcon(icon)
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/newPrefix/girl_icon_choosen.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.girlButton.setIcon(icon)

    def connectClicked(self):  # 加入聊天安紐
        self.waitingText.setText('等待其他人加入中....')
        self.userText.clear()
        self.textArea.clear()
        # 檢查18+
        if self.over18Mode.isChecked():
            self.ZONE = 'L'
        else:
            self.ZONE = 'N'

        try:
            self.socket = socket(AF_INET, SOCK_STREAM)
            self.socket.connect((self.serverName, self.serverPort))
        except ConnectionRefusedError:  # 如果連不上server顯示錯誤訊息
            errorThread = threading.Thread(target=self.showError)
            errorThread.start()
        else:
            self.stackedWidget.setCurrentIndex(1)
            waitThread = threading.Thread(target=self.handleWaiting)
            self.thread = waitThread
            waitThread.setDaemon(True)
            waitThread.start()
        finally:
            print("connect clicked")

    def handleWaiting(self):  # 處理加房間
        self.chatWidget.setHidden(True)
        self.reconnectButton.setHidden(True)
        self.waitingText.setText('等待其他人加入中....')
        try:
            # 分配是否18+
            ZONEMSGEXCHANGE = False
            while ZONEMSGEXCHANGE == False:
                self.socket.send((self.ZONE + "ZONEMSGEXCGANGETIMEANDWAITINGFORNEWCLIENTSCHATZONE").encode())
                Client_ZONE = ""
                while Client_ZONE.find("ZONEMSGEXCGANGETIMEANDWAITINGFORNEWCLIENTSCHATZONEOK") == -1:
                    Client_ZONE = self.socket.recv(1024).decode()
                ZONEMSGEXCHANGE = True
            # 分配完畢
            P_msg = self.socket.recv(1024).decode()
            # 開始接收聊天訊息
            if P_msg == 'PERSONTWOHASCAMEINTHECHATROOM':
                self.P2connection = True
            if self.P2connection:
                self.__listening(self.socket)
            else:
                self.P2connection = self.wait_for_P2(self.socket)
                if self.P2connection:
                    self.__listening(self.socket)
        except:
            print('some error happen')
        finally:
            self.P2connection = False
            self.chatWidget.setHidden(True)
            self.waitingWidget.setHidden(False)
            self.waitingText.setText('與伺服器連線中斷 點擊下方按鈕嘗試重新連線')
            self.reconnectButton.setHidden(False)
            print('waiting thread close')

    def wait_for_P2(self, clientSocket):
        try:
            while True:
                P2msg = clientSocket.recv(1024)
                if P2msg.decode() == 'PERSONTWOHASCAMEINTHECHATROOM':  # wait for P2
                    break
            return True
        except:
            return False

    def showError(self):  # 顯示連不上伺服器
        try:
            self.errorMessage.setHidden(False)
            time.sleep(2)
            self.errorMessage.setHidden(True)
        except:
            pass
        finally:
            print('errorThread stop!')

    def exitClicked(self):  # 離開按鈕
        self.stackedWidget.setCurrentIndex(0)
        self.socket.close()

    def sendClicked(self):  # 傳送訊息按鈕
        self.socket.send(self.textArea.toPlainText().encode())
        self.userText.setText(self.textArea.toPlainText())
        self.textArea.clear()

    def __listening(self, clientSocket):
        ROOMMSGEXCHANGE = False
        try:
            while ROOMMSGEXCHANGE == False:  # 交換房間資訊
                clientSocket.send((self.SEX + "ROOMMSGEXCHANGEANDSENDTOANOTHER").encode())
                RoomMsg = ""
                while True:
                    RoomMsg = clientSocket.recv(1024).decode()
                    if RoomMsg.find("ROOMMSGEXCHANGEANDSENDTOANOTHER")!=-1:
                        break
                    elif RoomMsg=='ROOMMATEDISCONNECTTOSERVER':
                        self.P2connection = False
                        canvas.itemconfig(ct2,text='P2 quit this room Please reconnect to server')

                self.P2SEX = RoomMsg[0]
                # 取得對方性別後改變對方頭貼
                if self.P2SEX == 'G':
                    self.genderPicClient.setPixmap(QtGui.QPixmap(":/newPrefix/girl.png"))
                else:
                    self.genderPicClient.setPixmap(QtGui.QPixmap(":/newPrefix/boy.png"))
                # waiting畫面隱藏聊天畫面顯示
                self.waitingWidget.setHidden(True)
                self.chatWidget.setHidden(False)
                self.clientText.clear()
                ROOMMSGEXCHANGE = True
            while True:
                message = clientSocket.recv(1024)
                print(message.decode())
                if len(message) is 0:
                    break
                elif message.decode() == 'ROOMMATEDISCONNECTTOSERVER':  # 如果對方離開
                    self.P2connection = False
                    break
                else:
                    sentence = message.decode()
                    self.clientText.setText(sentence)
        except:
            self.P2connection = False
            self.chatWidget.setHidden(True)
            self.waitingWidget.setHidden(False)
            self.waitingText.setText('與伺服器連線中斷 點擊下方按鈕嘗試重新連線')
            self.reconnectButton.setHidden(False)
            print('listening some error happen')
            pass
        finally:
            self.P2connection = False
            self.chatWidget.setHidden(True)
            self.waitingWidget.setHidden(False)
            self.waitingText.setText('與伺服器連線中斷 點擊下方按鈕嘗試重新連線')
            self.reconnectButton.setHidden(False)
            print('thread stop!!')


if __name__ == '__main__':
    serverName = '127.0.0.1'
    serverPort = 5000
    app = QApplication(sys.argv)
    MainWindow = MainWindow(serverName, serverPort)
    MainWindow.show()
    MainWindow.stackedWidget.setCurrentIndex(0)
    sys.exit(app.exec_())
