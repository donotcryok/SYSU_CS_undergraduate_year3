#include <stdio.h>
#include <winsock2.h>
#include <windows.h>

#pragma comment(lib, "ws2_32.lib") // 链接Winsock库

#define RECV_PORT 8888 // 接收端监听的端口号，可以自行修改
#define PACKET_COUNT 100 // 期望接收的数据包总数

int main() {
    WSADATA wsaData;
    SOCKET recvSocket;
    struct sockaddr_in recvAddr, senderAddr;
    int senderAddrSize = sizeof(senderAddr);
    int recvLen;
    char recvBuf[1024];
    int receivedPackets[PACKET_COUNT + 1] = {0}; // 数组用于标记收到的包，索引从1到100
    int i, lostCount = 0;
    int packetID;

    // 初始化Winsock
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        printf("WSAStartup failed with error %d\n", WSAGetLastError());
        return 1;
    }

    // 创建UDP socket
    recvSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (recvSocket == INVALID_SOCKET) {
        printf("socket() failed with error %d\n", WSAGetLastError());
        WSACleanup();
        return 1;
    }

    // 绑定接收端的地址和端口
    recvAddr.sin_family = AF_INET;
    recvAddr.sin_port = htons(RECV_PORT);
    recvAddr.sin_addr.s_addr = htonl(INADDR_ANY); // 监听所有网络接口

    if (bind(recvSocket, (SOCKADDR*)&recvAddr, sizeof(recvAddr)) == SOCKET_ERROR) {
        printf("bind() failed with error %d\n", WSAGetLastError());
        closesocket(recvSocket);
        WSACleanup();
        return 1;
    }

    printf("Receiver is running on 172.16.27.2:%d...\nWaiting for packets...\n", RECV_PORT);

    // 设置超时时间（5秒）
    // 如果5秒内没有收到任何数据，recvfrom将返回，避免程序永远阻塞
    DWORD timeout = 5000;
    setsockopt(recvSocket, SOL_SOCKET, SO_RCVTIMEO, (char*)&timeout, sizeof(timeout));

    // 接收数据包
    while (1) {
        recvLen = recvfrom(recvSocket, recvBuf, sizeof(recvBuf), 0, (SOCKADDR*)&senderAddr, &senderAddrSize);
        if (recvLen == SOCKET_ERROR) {
            int error = WSAGetLastError();
            if (error == WSAETIMEDOUT) {
                printf("\nNo data received for 5 seconds. Stopping reception.\n");
                break;
            } else {
                printf("recvfrom() failed with error %d\n", error);
                continue;
            }
        }

        // 确保接收到的数据足以包含一个整数（我们的包ID）
        if (recvLen >= sizeof(int)) {
            // 从接收缓冲区的前4个字节中提取包ID
            packetID = *((int*)recvBuf);
            if (packetID >= 1 && packetID <= PACKET_COUNT) {
                receivedPackets[packetID] = 1; // 标记这个包已收到
                printf("Received packet with ID: %d\n", packetID);
            }
        } else {
            printf("Received a packet with invalid length.\n");
        }
    }

    // 统计丢失的包
    for (i = 1; i <= PACKET_COUNT; i++) {
        if (receivedPackets[i] == 0) {
            lostCount++;
            printf("Packet %d was lost.\n", i);
        }
    }

    // 输出结果
    printf("\n===== Statistics =====\n");
    printf("Expected packets: %d\n", PACKET_COUNT);
    printf("Received packets: %d\n", PACKET_COUNT - lostCount);
    printf("Lost packets: %d\n", lostCount);
    printf("Packet loss rate: %.2f%%\n", (lostCount * 100.0) / PACKET_COUNT);

    // 清理
    closesocket(recvSocket);
    WSACleanup();

    printf("Press any key to exit...\n");
    getchar();
    return 0;
}