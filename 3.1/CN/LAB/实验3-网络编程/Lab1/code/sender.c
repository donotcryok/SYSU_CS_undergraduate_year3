#include <stdio.h>
#include <winsock2.h>
#include <windows.h>

#pragma comment(lib, "ws2_32.lib") // 链接Winsock库

#define DEST_IP "172.16.27.2"   // 接收端的IP地址
#define DEST_PORT 8888          // 接收端的端口号，必须与接收端程序一致
#define PACKET_COUNT 100        // 要发送的数据包数量
#define SEND_DELAY 10           // 发送每个包之间的延迟（毫秒），可调整以模拟网络状况

int main() {
    WSADATA wsaData;
    SOCKET sendSocket;
    struct sockaddr_in destAddr;
    int i;
    char sendBuf[1024];
    int packetID;

    // 初始化Winsock
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        printf("WSAStartup failed with error %d\n", WSAGetLastError());
        return 1;
    }

    // 创建UDP socket
    sendSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sendSocket == INVALID_SOCKET) {
        printf("socket() failed with error %d\n", WSAGetLastError());
        WSACleanup();
        return 1;
    }

    // 设置目标地址（接收端）
    destAddr.sin_family = AF_INET;
    destAddr.sin_port = htons(DEST_PORT);
    destAddr.sin_addr.s_addr = inet_addr(DEST_IP); // 接收端的IP

    printf("Sender is ready. Sending %d packets to %s:%d...\n", PACKET_COUNT, DEST_IP, DEST_PORT);

    for (i = 1; i <= PACKET_COUNT; i++) {
        packetID = i;
        // 将包ID（一个整数）拷贝到发送缓冲区的开头
        // 这样接收端可以通过解析前4个字节来知道这是第几个包
        memcpy(sendBuf, &packetID, sizeof(packetID));

        // 发送数据包
        if (sendto(sendSocket, sendBuf, sizeof(packetID), 0, (SOCKADDR*)&destAddr, sizeof(destAddr)) == SOCKET_ERROR) {
            printf("sendto() failed for packet %d with error %d\n", i, WSAGetLastError());
        } else {
            printf("Sent packet with ID: %d\n", i);
        }

        // 短暂延迟，避免洪水式发送导致网络或接收端处理不过来
        Sleep(SEND_DELAY);
    }

    printf("\nAll packets sent.\n");

    // 清理
    closesocket(sendSocket);
    WSACleanup();

    printf("Press any key to exit...\n");
    getchar();
    return 0;
}