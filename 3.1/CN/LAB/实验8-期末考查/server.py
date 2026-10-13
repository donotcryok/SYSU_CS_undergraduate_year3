import socket
import struct
import hashlib
import os

# 配置
SERVER_IP = '0.0.0.0'  # 监听所有网卡
SERVER_PORT = 9999
SAVE_DIR = 'received_files'

def calculate_md5(data):
    return hashlib.md5(data).hexdigest()

def start_server():
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    # 创建 TCP Socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen(1)
    
    print(f"[*] Server listening on {SERVER_IP}:{SERVER_PORT}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"[+] Accepted connection from {addr}")

        try:
            # 1. 接收文本长度 (4 bytes)
            raw_text_len = recv_all(client_socket, 4)
            if not raw_text_len: break
            text_len = struct.unpack('!I', raw_text_len)[0]

            # 2. 接收文本内容
            text_data = recv_all(client_socket, text_len)
            text_content = text_data.decode('utf-8')
            print(f"[R] Received Text:\n{text_content}\n")
            
            # 保存文本
            with open(os.path.join(SAVE_DIR, 'received_text.txt'), 'w', encoding='utf-8') as f:
                f.write(text_content)

            # 3. 接收图片长度 (4 bytes)
            raw_img_len = recv_all(client_socket, 4)
            img_len = struct.unpack('!I', raw_img_len)[0]

            # 4. 接收图片内容
            print(f"[*] Expecting image size: {img_len} bytes")
            img_data = recv_all(client_socket, img_len)
            
            # 5. 接收客户端计算的 MD5 (32 bytes hex string)
            client_md5 = recv_all(client_socket, 32).decode('utf-8')

            # 验证完整性
            server_md5 = calculate_md5(img_data)
            print(f"[V] Client MD5: {client_md5}")
            print(f"[V] Server MD5: {server_md5}")

            if client_md5 == server_md5:
                print("[+] Integrity Check: PASSED")
            else:
                print("[-] Integrity Check: FAILED")

            # 保存图片
            save_path = os.path.join(SAVE_DIR, 'received_image.bmp')
            with open(save_path, 'wb') as f:
                f.write(img_data)
            print(f"[+] Image saved to {save_path}")

            # 发送确认
            client_socket.send(b"ACK: Transfer Complete")

        except Exception as e:
            print(f"[-] Error: {e}")
        finally:
            client_socket.close()
            print("[-] Connection closed")
            break # 实验演示通常接收一次即可，或者去掉 break 持续监听

def recv_all(sock, n):
    """Helper function to recv n bytes or return None if EOF is hit"""
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data

if __name__ == '__main__':
    start_server()
