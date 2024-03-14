import cv2, imutils, socket
import numpy as np
import time
import threading, pyaudio, pickle, struct, queue, os, base64

q = queue.Queue(maxsize=10)

vid = cv2.VideoCapture(0)

BUFF_SIZE = 65536
server_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,BUFF_SIZE)
host_name = socket.gethostname()
host_ip = '192.168.43.210'
print(host_ip)
port = 80
socket_address = (host_ip,port)
server_socket.bind(socket_address)
print('Listening at:',socket_address)

def generate_video():
    WIDTH=400
    while(vid.isOpened()):
        try:
            _,frame = vid.read()
            frame = imutils.resize(frame,width=WIDTH)
            q.put(frame)
        except:
            os._exit(1)
        time.sleep(0.001)
    print('Player closed')
    vid.release()
	
def send_video():
    fps,st,frames_to_count,cnt = (0,0,20,0)
    cv2.namedWindow('SERVER TRANSMITTING VIDEO')        
    cv2.moveWindow('SERVER TRANSMITTING VIDEO', 400,30) 
    msg,client_addr = server_socket.recvfrom(BUFF_SIZE)
    print('connection from ',client_addr)
    WIDTH=400
    while(True):
        frame = q.get()
        encoded,buffer = cv2.imencode('.jpeg',frame,[cv2.IMWRITE_JPEG_QUALITY,80])
        message = base64.b64encode(buffer)
        server_socket.sendto(message,client_addr)
        frame = cv2.putText(frame,'FPS: '+str(round(fps,1)),(10,40),
                            cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)
        
        if cnt == frames_to_count:
            try:
                fps = round(frames_to_count/(time.time()-st),1)
                st=time.time()
                cnt=0
            except:
                pass
        cnt+=1
        cv2.imshow('SERVER TRANSMITTING VIDEO', frame)
        key = cv2.waitKey(1) & 0xFF	
        if key == ord('q'):
            os._exit(1)
        time.sleep(0.01)   

def send_message():
    s = socket.socket()
    s.bind((host_ip, (port-1)))
    s.listen(5)
    client_socket,addr = s.accept()
    cnt=0
    while True:
        if client_socket:
            while True:
                print('SERVER: ')
                data = input ()
                a = pickle.dumps(data)
                message = struct.pack("Q",len(a))+a
                client_socket.sendall(message)
           
                cnt+=1
                time.sleep(0.01)
                
        

def get_message():
    s = socket.socket()
    s.bind((host_ip, (port-2)))
    s.listen(5)
    client_socket,addr = s.accept()
    data = b""
    payload_size = struct.calcsize("Q")
    
    while True:
        try:
            while len(data) < payload_size:
                packet = client_socket.recv(4*1024) # 4K
                if not packet: break
                data+=packet
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("Q",packed_msg_size)[0]
            while len(data) < msg_size:
                data += client_socket.recv(4*1024)
            frame_data = data[:msg_size]
            data  = data[msg_size:]
            frame = pickle.loads(frame_data)
            print('',end='\n')
            print('CLIENT:',frame,end='\n')
            print('SERVER:')
            time.sleep(0.001)

        except Exception as e:
            print('Dropped...')
            time.sleep(2)
            pass

            client_socket.close()
            print('Audio closed')
    
        


def get_video():
    cv2.namedWindow('SERVER RECEIVING VIDEO')        
    cv2.moveWindow('SERVER RECEIVING VIDEO', 400,360) 
    fps,st,frames_to_count,cnt = (0,0,20,0)
    BUFF_SIZE = 65536
    server_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,BUFF_SIZE)
    socket_address = (host_ip,port-3)
    server_socket.bind(socket_address)

    while True:
        packet,_ = server_socket.recvfrom(BUFF_SIZE)
        data = base64.b64decode(packet,' /')
        npdata = np.frombuffer(data,dtype=np.uint8)

        frame = cv2.imdecode(npdata,1)
        frame = cv2.putText(frame,'FPS: '+str(fps),(10,40),
                            cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)
        cv2.imshow("SERVER RECEIVING VIDEO",frame)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            server_socket.close()
            break
            
        if cnt == frames_to_count:
            try:
                fps = round(frames_to_count/(time.time()-st),1)
                st=time.time()
                cnt=0
            except:
                pass
        cnt+=1
        time.sleep(0.001)
    server_socket.close()
    cv2.destroyAllWindows() 

def get_audio():
        
    p = pyaudio.PyAudio()
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    output=True,
                    frames_per_buffer=CHUNK)

    with socket.socket() as server_socket:
        server_socket.bind((host_ip, port-4))
        server_socket.listen(2)
        conn, address = server_socket.accept()
        print("Connection from " + address[0] + ":" + str(address[1]))
        data = conn.recv(CHUNK)
        while data != "":
            try:
                data = conn.recv(CHUNK)
                stream.write(data)
            except socket.error:
                print("Client Disconnected")
                break

    stream.stop_stream()
    stream.close()
    p.terminate()
                    
t1 = threading.Thread(target=send_message, args=())
t2 = threading.Thread(target=get_message, args=())
t3 = threading.Thread(target=generate_video, args=())
t4 = threading.Thread(target=send_video, args=())
t5 = threading.Thread(target=get_video, args=())
t6 = threading.Thread(target=get_audio, args=())

t1.start()
t2.start()
t3.start()
t4.start()
t5.start()
t6.start()

