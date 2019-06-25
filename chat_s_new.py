from socket import *
import threading
import sys
import flask
from flask import Flask, request, abort, render_template
from time import sleep

class Client:
    def __init__(self, client_socket, address, client_num, client_zone):
        self.cs = client_socket
        self.addr = address
        self.cnum = client_num
        self.zone = client_zone
        
    def send(self, msg):
        try:
            self.cs.send(msg.encode())
        except Exception as e:
            # print("cleint send: "+str(e))
            return False
        return True
        
    def __str__(self):
        return "client_{}".format(self.cnum)
        
    def getpeername(self):
        return self.cs.getpeername()
    
    def wait_for_msg(self):
        return self.cs.recv(1024)
        
class MultithreadingTCPServer:
    def __init__(self, name, port):
        self.clients =list()
        self.serverName = name
        self.serverPort = port
        self.client_num = 0
        self.room_num = 0
        self.normal_waiting_client = list()
        self.limit_waiting_client = list()
        
    def start(self):
        try:
            with socket(AF_INET, SOCK_STREAM) as serverSocket:
                print('Bind server socket to', self.serverName, ':', self.serverPort)
                serverSocket.bind((self.serverName, self.serverPort))
                serverSocket.listen(1)
                print('Multithreading server binding success')
                while True:
                    print('Waiting for new client')
                    new_client = self.wait_for_new_client( serverSocket )  # 不斷等待新的Client 再將其分配位子
                    if  new_client != None:
                        if new_client.zone=="N":  # 普通房間的 client
                            if len(self.normal_waiting_client)==0:
                                if self.send_msg_to_client(new_client,'1'):  # 成功送訊息給P1 才算連線成功 才創造進入等候位子
                                    self.normal_waiting_client.append(new_client)
                            else:
                                c1=self.normal_waiting_client[0]
                                self.normal_waiting_client.remove(c1)
                                c2=new_client
                                
                                self.send_msg_to_client(c1,'PERSONTWOHASCAMEINTHECHATROOM')
                                self.send_msg_to_client(c2,'PERSONTWOHASCAMEINTHECHATROOM')
                                self.create_new_room(c1, c2)
                        else:                     # 限制級房間的 client
                            if len(self.limit_waiting_client)==0:
                                if self.send_msg_to_client(new_client,'1'):  # 成功送訊息給P1 才算連線成功 才創造進入等候位子
                                    self.limit_waiting_client.append(new_client)
                            else:
                                c1=self.limit_waiting_client[0]
                                self.limit_waiting_client.remove(c1)
                                c2=new_client
                                
                                self.send_msg_to_client(c1,'PERSONTWOHASCAMEINTHECHATROOM')
                                self.send_msg_to_client(c2,'PERSONTWOHASCAMEINTHECHATROOM')
                                self.create_new_room(c1, c2)
                            
        except Exception as e:
            print(e)
            
        finally:
            print('Server shutdown.')

    def create_new_room(self, c1, c2):
        self.room_num+=1
        thread = threading.Thread(target = self.__handleRoom, args = (c1, c2, self.room_num,))
        thread.start()
        
    def wait_for_new_client(self, serverSocket):
        client_socket, address = serverSocket.accept()
        #交換區域訊息(18+ OR 一般房間)
        try:
            ZONEMSGEXCHANGE=False
            while ZONEMSGEXCHANGE==False:  # 交換房間資訊
                ZONE_MSG = client_socket.recv(1024).decode()  #等待client送房間資訊來
                if ZONE_MSG.find("ZONEMSGEXCGANGETIMEANDWAITINGFORNEWCLIENTSCHATZONE")!=-1:
                    Client_ZONE = ZONE_MSG[0]
                    client_socket.send("ZONEMSGEXCGANGETIMEANDWAITINGFORNEWCLIENTSCHATZONEOK".encode())
                    # print("得到對方的性別")
                    ZONEMSGEXCHANGE=True

        except Exception as e:
            print("連接新的Client失敗: "+str(e))
            client_socket.close()
            return None
            
        self.client_num+=1
        new_client = Client(client_socket, address, self.client_num , Client_ZONE)
        print(str(new_client)+" connected")
        self.clients.append(new_client)
        return new_client
        
    def send_msg_to_client(self, client, msg):
        # print("嘗試送: "+msg+" 給 "+str(client))
        if client.send(msg):
            return True
        else:
            self.disconnect_client(client)
            return False
        
        
    def disconnect_client(self, client):
        # print(str(client)+" disonnected")
        try:
            client.close()
        except:
            pass
        if client in self.clients:
            self.clients.remove(client)
        
    def __handleRoom(self, c1, c2, room):
        print("Room_{} created for ".format(self.room_num)+str(c1)+" and "+str(c2))

        c1_name, c1_port = c1.getpeername()
        c2_name, c2_port = c2.getpeername()
        # print('P1 '+str(c1)+" ", c1_name, c1_port)
        # print('P2 '+str(c2)+" ", c2_name, c2_port)
        
        results = [True, True]
        thread_1_to_2 = threading.Thread(target = self.pass_msg, args = (c1,c2,results,0,))
        thread_1_to_2.start()
        
        thread_2_to_1 = threading.Thread(target = self.pass_msg, args = (c2,c1,results,1,))
        thread_2_to_1.start()
        
        while results[0] and results[1]:
            sleep(1)
            pass
            
        results[0]=False
        results[1]=False

        self.disconnect_client(c1)
        self.disconnect_client(c2)
        print('Room ', room, ' shutdown')

    def pass_msg(self, from_c, to_c, results, i):
        ROOMMSGEXCHANGE=False
        try:
            while results[i] and ROOMMSGEXCHANGE==False:  # 交換房間資訊
                ROOM_MSG = from_c.wait_for_msg().decode()  #等待client送房間資訊來
                if ROOM_MSG.find("ROOMMSGEXCHANGEANDSENDTOANOTHER")!=-1:
                    FROM_SEX = ROOM_MSG[0]
                    to_c.send(FROM_SEX+"ROOMMSGEXCHANGEANDSENDTOANOTHER")
                    # print("得到對方的性別")
                    ROOMMSGEXCHANGE=True
            while results[i]:
                from_msg = from_c.wait_for_msg()
                if len(from_msg) == 0:
                    break
                s = from_msg.decode()

                if to_c.send(s)==False:
                    results[i]=False
                    results[(i+1)%2]=False
        except Exception as e:
            print("P{} close window".format(i+1))
            # print("e_p "+str(e))
            to_c.send('ROOMMATEDISCONNECTTOSERVER')

        finally:
            results[(i+1)%2]=False
            results[i] = False
            self.disconnect_client(from_c)
            self.disconnect_client(to_c)


if __name__=="__main__":
    serverName = '127.0.0.1'
    serverPort = 5000

    server = MultithreadingTCPServer(serverName, serverPort)
    server.start()

