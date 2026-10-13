#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <winsock2.h>
#include <windows.h>
#include <process.h>

#pragma comment(lib, "ws2_32.lib")

#define MAX_CLIENTS 10
#define BUFFER_SIZE 1024
#define SERVER_PORT 8889

// 客户端信息结构
typedef struct {
    SOCKET socket;
    struct sockaddr_in addr;
    int id;
    char username[50];
    int active;
} ClientInfo;

// 全局变量
ClientInfo clients[MAX_CLIENTS];
int clientCount = 0;
CRITICAL_SECTION clientsLock;

// 函数声明
unsigned __stdcall handleClient(void* arg);
void broadcastMessage(char* message, int senderID);
void removeClient(int clientID);
int addClient(SOCKET clientSocket, struct sockaddr_in clientAddr);

int main() {
    WSADATA wsaData;
    SOCKET serverSocket, clientSocket;
    struct sockaddr_in serverAddr, clientAddr;
    int clientAddrSize = sizeof(clientAddr);
    
    printf("=== TCP聊天服务器 ===\n");
    
    // 初始化Winsock
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        printf("WSAStartup failed with error %d\n", WSAGetLastError());
        return 1;
    }
    
    // 初始化临界区
    InitializeCriticalSection(&clientsLock);
    
    // 初始化客户端数组
    for (int i = 0; i < MAX_CLIENTS; i++) {
        clients[i].active = 0;
    }
    
    // 创建TCP socket
    serverSocket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (serverSocket == INVALID_SOCKET) {
        printf("socket() failed with error %d\n", WSAGetLastError());
        WSACleanup();
        return 1;
    }
    
    // 设置服务器地址
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_addr.s_addr = INADDR_ANY;
    serverAddr.sin_port = htons(SERVER_PORT);
    
    // 绑定socket
    if (bind(serverSocket, (SOCKADDR*)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR) {
        printf("bind() failed with error %d\n", WSAGetLastError());
        closesocket(serverSocket);
        WSACleanup();
        return 1;
    }
    
    // 开始监听
    if (listen(serverSocket, SOMAXCONN) == SOCKET_ERROR) {
        printf("listen() failed with error %d\n", WSAGetLastError());
        closesocket(serverSocket);
        WSACleanup();
        return 1;
    }
    
    printf("服务器启动成功，监听端口 %d\n", SERVER_PORT);
    printf("等待客户端连接...\n\n");
    
    // 主循环：接受客户端连接
    while (1) {
        clientSocket = accept(serverSocket, (SOCKADDR*)&clientAddr, &clientAddrSize);
        if (clientSocket == INVALID_SOCKET) {
            printf("accept() failed with error %d\n", WSAGetLastError());
            continue;
        }
        
        // 添加新客户端
        int clientID = addClient(clientSocket, clientAddr);
        if (clientID == -1) {
            printf("服务器已满，拒绝连接 %s:%d\n", 
                   inet_ntoa(clientAddr.sin_addr), ntohs(clientAddr.sin_port));
            closesocket(clientSocket);
            continue;
        }
        
        printf("新客户端连接: ID=%d, IP=%s:%d\n", 
               clientID, inet_ntoa(clientAddr.sin_addr), ntohs(clientAddr.sin_port));
        
        // 为每个客户端创建处理线程
        HANDLE hThread = (HANDLE)_beginthreadex(NULL, 0, handleClient, &clients[clientID], 0, NULL);
        if (hThread == NULL) {
            printf("创建线程失败\n");
            removeClient(clientID);
        } else {
            CloseHandle(hThread);
        }
    }
    
    // 清理
    closesocket(serverSocket);
    DeleteCriticalSection(&clientsLock);
    WSACleanup();
    
    return 0;
}

// 添加客户端到数组
int addClient(SOCKET clientSocket, struct sockaddr_in clientAddr) {
    EnterCriticalSection(&clientsLock);
    
    for (int i = 0; i < MAX_CLIENTS; i++) {
        if (!clients[i].active) {
            clients[i].socket = clientSocket;
            clients[i].addr = clientAddr;
            clients[i].id = i + 1;
            clients[i].active = 1;
            strcpy(clients[i].username, "未命名");
            clientCount++;
            
            LeaveCriticalSection(&clientsLock);
            return i;
        }
    }
    
    LeaveCriticalSection(&clientsLock);
    return -1; // 服务器已满
}

// 从数组中移除客户端
void removeClient(int clientID) {
    EnterCriticalSection(&clientsLock);
    
    if (clientID >= 0 && clientID < MAX_CLIENTS && clients[clientID].active) {
        closesocket(clients[clientID].socket);
        clients[clientID].active = 0;
        clientCount--;
        printf("客户端 %s (ID=%d) 已断开连接\n", 
               clients[clientID].username, clients[clientID].id);
    }
    
    LeaveCriticalSection(&clientsLock);
}

// 广播消息给所有客户端
void broadcastMessage(char* message, int senderID) {
    EnterCriticalSection(&clientsLock);
    
    for (int i = 0; i < MAX_CLIENTS; i++) {
        if (clients[i].active && i != senderID) {
            if (send(clients[i].socket, message, strlen(message), 0) == SOCKET_ERROR) {
                printf("发送消息到客户端 %d 失败\n", clients[i].id);
            }
        }
    }
    
    LeaveCriticalSection(&clientsLock);
}

// 处理客户端连接的线程函数
unsigned __stdcall handleClient(void* arg) {
    ClientInfo* client = (ClientInfo*)arg;
    char buffer[BUFFER_SIZE];
    int bytesReceived;
    char welcomeMsg[BUFFER_SIZE];
    char broadcastMsg[BUFFER_SIZE];
    
    // 发送欢迎消息
    sprintf(welcomeMsg, "欢迎连接到TCP聊天服务器！您的ID是: %d\n请输入您的用户名: ", client->id);
    send(client->socket, welcomeMsg, strlen(welcomeMsg), 0);
    
    // 接收用户名
    bytesReceived = recv(client->socket, buffer, BUFFER_SIZE - 1, 0);
    if (bytesReceived > 0) {
        buffer[bytesReceived] = '\0';
        // 移除换行符
        char* newline = strchr(buffer, '\n');
        if (newline) *newline = '\0';
        newline = strchr(buffer, '\r');
        if (newline) *newline = '\0';
        
        if (strlen(buffer) > 0) {
            strcpy(client->username, buffer);
            printf("客户端 ID=%d 设置用户名为: %s\n", client->id, client->username);
            
            // 通知所有客户端有新用户加入
            sprintf(broadcastMsg, "*** %s 加入了聊天室 ***\n", client->username);
            broadcastMessage(broadcastMsg, client - clients);
            
            sprintf(welcomeMsg, "用户名设置成功！开始聊天吧（输入 'quit' 退出）:\n");
            send(client->socket, welcomeMsg, strlen(welcomeMsg), 0);
        }
    }
    
    // 处理客户端消息
    while (1) {
        bytesReceived = recv(client->socket, buffer, BUFFER_SIZE - 1, 0);
        
        if (bytesReceived <= 0) {
            // 客户端断开连接
            break;
        }
        
        buffer[bytesReceived] = '\0';
        
        // 移除换行符
        char* newline = strchr(buffer, '\n');
        if (newline) *newline = '\0';
        newline = strchr(buffer, '\r');
        if (newline) *newline = '\0';
        
        // 检查是否是退出命令
        if (strcmp(buffer, "quit") == 0) {
            sprintf(broadcastMsg, "*** %s 离开了聊天室 ***\n", client->username);
            broadcastMessage(broadcastMsg, client - clients);
            break;
        }
        
        // 显示收到的消息
        printf("[%s]: %s\n", client->username, buffer);
        
        // 广播消息给其他客户端
        sprintf(broadcastMsg, "[%s]: %s\n", client->username, buffer);
        broadcastMessage(broadcastMsg, client - clients);
    }
    
    // 清理客户端
    removeClient(client - clients);
    
    return 0;
}