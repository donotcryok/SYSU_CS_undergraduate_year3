#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <winsock2.h>
#include <windows.h>
#include <process.h>
#include <conio.h>

#pragma comment(lib, "ws2_32.lib")

#define BUFFER_SIZE 1024
#define SERVER_IP "172.16.27.2"  // 本地测试，可以修改为实际服务器IP
#define SERVER_PORT 8889

// 全局变量
SOCKET clientSocket;
int running = 1;

// 函数声明
unsigned __stdcall receiveMessages(void* arg);

int main() {
    WSADATA wsaData;
    struct sockaddr_in serverAddr;
    char sendBuffer[BUFFER_SIZE];
    char username[50];
    
    printf("=== TCP聊天客户端 ===\n");
    
    // 初始化Winsock
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        printf("WSAStartup failed with error %d\n", WSAGetLastError());
        return 1;
    }
    
    // 创建TCP socket
    clientSocket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (clientSocket == INVALID_SOCKET) {
        printf("socket() failed with error %d\n", WSAGetLastError());
        WSACleanup();
        return 1;
    }
    
    // 设置服务器地址
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(SERVER_PORT);
    serverAddr.sin_addr.s_addr = inet_addr(SERVER_IP);
    
    printf("连接到服务器 %s:%d...\n", SERVER_IP, SERVER_PORT);
    
    // 连接到服务器
    if (connect(clientSocket, (SOCKADDR*)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR) {
        printf("连接服务器失败，错误代码: %d\n", WSAGetLastError());
        printf("请确保服务器正在运行并且IP地址正确\n");
        closesocket(clientSocket);
        WSACleanup();
        printf("按任意键退出...\n");
        _getch();
        return 1;
    }
    
    printf("成功连接到服务器！\n\n");
    
    // 创建接收消息的线程
    HANDLE hReceiveThread = (HANDLE)_beginthreadex(NULL, 0, receiveMessages, NULL, 0, NULL);
    if (hReceiveThread == NULL) {
        printf("创建接收线程失败\n");
        closesocket(clientSocket);
        WSACleanup();
        return 1;
    }
    
    // 主循环：发送消息
    while (running) {
        printf("输入消息 (输入 'quit' 退出): ");
        if (fgets(sendBuffer, sizeof(sendBuffer), stdin) != NULL) {
            // 移除换行符
            char* newline = strchr(sendBuffer, '\n');
            if (newline) *newline = '\0';
            
            // 检查是否要退出
            if (strcmp(sendBuffer, "quit") == 0) {
                running = 0;
                break;
            }
            
            // 发送消息到服务器
            if (send(clientSocket, sendBuffer, strlen(sendBuffer), 0) == SOCKET_ERROR) {
                printf("发送消息失败，错误代码: %d\n", WSAGetLastError());
                running = 0;
                break;
            }
        }
    }
    
    printf("\n正在断开连接...\n");
    
    // 等待接收线程结束
    WaitForSingleObject(hReceiveThread, 2000);
    CloseHandle(hReceiveThread);
    
    // 清理
    closesocket(clientSocket);
    WSACleanup();
    
    printf("已断开连接。按任意键退出...\n");
    _getch();
    
    return 0;
}

// 接收消息的线程函数
unsigned __stdcall receiveMessages(void* arg) {
    char buffer[BUFFER_SIZE];
    int bytesReceived;
    
    while (running) {
        bytesReceived = recv(clientSocket, buffer, BUFFER_SIZE - 1, 0);
        
        if (bytesReceived <= 0) {
            if (running) {
                printf("\n与服务器的连接已断开\n");
                running = 0;
            }
            break;
        }
        
        buffer[bytesReceived] = '\0';
        printf("%s", buffer);
        
        // 如果消息包含用户名提示，则不显示输入提示
        if (strstr(buffer, "请输入您的用户名") == NULL && 
            strstr(buffer, "输入消息") == NULL) {
            if (running && strstr(buffer, "开始聊天吧") == NULL) {
                // 不重复显示输入提示
            }
        }
    }
    
    return 0;
}