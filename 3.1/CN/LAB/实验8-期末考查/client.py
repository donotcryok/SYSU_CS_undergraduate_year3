import socket
import struct
import hashlib
import os
import sys

# 配置
SERVER_IP = '192.168.50.5' # 目标主机 H5 的 IP，实验时请根据实际情况修改
SERVER_PORT = 9999
IMAGE_PATH = 'image.bmp'   # 需确保目录下有此文件

TEXT_CONTENT = """Dr. Sun Yat-sen ordered the merger of several colleges and universities in February 1924, into the National Guangdong University, which was renamed as National Sun Yat-sen University in his memory in August 1926."""

def calculate_md5(data):
    return hashlib.md5(data).hexdigest()

def start_client():
    # 检查图片是否存在
    if not os.path.exists(IMAGE_PATH):
        print(f"[-] Error: {IMAGE_PATH} not found. Please place a BMP file named '{IMAGE_PATH}' in the same directory.")
        # 创建一个伪造的 BMP 用于测试（如果文件不存在）
        with open(IMAGE_PATH, 'wb') as f:
            f.write(b'BM' + b'\x00'*52) # Minimal BMP header
        print(f"[!] Created dummy {IMAGE_PATH} for testing.")

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"[*] Connecting to {SERVER_IP}:{SERVER_PORT}...")
        client_socket.connect((SERVER_IP, SERVER_PORT))
        print("[+] Connected.")

        # 准备数据
        text_bytes = TEXT_CONTENT.encode('utf-8')
        with open(IMAGE_PATH, 'rb') as f:
            img_bytes = f.read()
        
        img_md5 = calculate_md5(img_bytes)

        # 1. 发送文本长度 (4 bytes)
        print(f"[*] Sending Text ({len(text_bytes)} bytes)...")
        client_socket.send(struct.pack('!I', len(text_bytes)))
        
        # 2. 发送文本内容
        client_socket.send(text_bytes)

        # 3. 发送图片长度 (4 bytes)
        print(f"[*] Sending Image ({len(img_bytes)} bytes)...")
        client_socket.send(struct.pack('!I', len(img_bytes)))

        # 4. 发送图片内容
        client_socket.sendall(img_bytes)

        # 5. 发送 MD5 校验和
        print(f"[*] Sending MD5: {img_md5}")
        client_socket.send(img_md5.encode('utf-8'))

        # 接收确认
        response = client_socket.recv(1024)
        print(f"[S] Server Response: {response.decode()}")

    except ConnectionRefusedError:
        print("[-] Connection refused. Is the server running?")
    except Exception as e:
        print(f"[-] Error: {e}")
    finally:
        client_socket.close()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        SERVER_IP = sys.argv[1]
    start_client()
