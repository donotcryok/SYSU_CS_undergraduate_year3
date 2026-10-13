# TCP套接字数据通信拓展实验说明文档

## 实验概述
本实验实现了基于TCP套接字的客户端-服务器数据通信程序，支持多客户端同时连接，实现聊天室功能。

## 文件说明
- `extend.c` - 主程序，可选择运行服务器或客户端模式
- `extend.exe` - 编译后的可执行文件
- `tcp_server.c` - 独立的TCP服务器程序
- `tcp_client.c` - 独立的TCP客户端程序

## 程序功能特点

### 服务器端功能
1. **TCP Socket创建和配置**
   - 创建TCP套接字 (SOCK_STREAM)
   - 绑定到指定端口 (8889)
   - 监听客户端连接请求

2. **多客户端支持**
   - 支持最多10个客户端同时连接
   - 使用线程处理每个客户端连接
   - 线程安全的客户端管理

3. **数据通信功能**
   - 接收客户端消息
   - 广播消息给所有其他客户端
   - 处理客户端连接和断开

### 客户端功能
1. **TCP连接建立**
   - 连接到指定服务器IP和端口
   - 错误处理和重连机制

2. **双向数据通信**
   - 发送消息到服务器
   - 接收服务器广播的消息
   - 使用独立线程处理接收

## 使用方法

### 运行主程序
```bash
# 编译程序
gcc -o extend.exe extend.c -lws2_32

# 运行程序
./extend.exe
```

### 操作步骤
1. **启动服务器**
   - 运行程序选择选项1
   - 服务器将在端口8889上监听

2. **启动客户端**
   - 在另一个终端运行程序选择选项2
   - 输入用户名开始聊天
   - 可以启动多个客户端实例

3. **进行通信**
   - 在客户端输入消息按回车发送
   - 消息会广播给所有其他连接的客户端
   - 输入"quit"退出程序

## Wireshark数据包分析

### 启动Wireshark监控
1. 启动Wireshark软件
2. 选择网络接口（通常是以太网或WiFi）
3. 开始捕获数据包

### 过滤TCP流量
```
# 过滤本程序的TCP流量
tcp.port == 8889

# 过滤本地回环流量
ip.addr == 127.0.0.1 and tcp.port == 8889
```

### 分析要点
1. **三次握手**
   - SYN包：客户端发起连接
   - SYN-ACK包：服务器响应
   - ACK包：客户端确认连接

2. **数据传输**
   - PSH-ACK包：包含实际数据
   - 观察序列号和确认号变化
   - 分析数据包的大小和内容

3. **连接断开**
   - FIN包：主动关闭连接
   - ACK包：确认关闭

## 程序架构

### 服务器端架构
```
主线程 -> 监听连接请求
  |
  ├── 客户端线程1 -> 处理客户端1的消息
  ├── 客户端线程2 -> 处理客户端2的消息
  └── ...
```

## 核心代码内容介绍

本实验核心代码分为服务器端、客户端和主程序三部分，均采用Windows Socket API实现，关键点如下：

### 1. 服务器端（tcp_server.c/extend.c的服务器部分）

- **客户端管理**  
  使用`ClientInfo`结构体数组保存每个客户端的套接字、地址、用户名和状态。通过临界区（`CRITICAL_SECTION`）实现线程安全的并发管理。

```c
// 客户端信息结构体
typedef struct {
    SOCKET socket;
    struct sockaddr_in addr;
    int id;
    char username[50];
    int active;
} ClientInfo;
```

- **多线程处理与主循环**  
  每个新连接的客户端由独立线程处理，线程函数`handleClient`负责接收消息、广播消息和处理断开。

```c
// 主循环：接受客户端连接
while (1) {
    clientSocket = accept(serverSocket, (SOCKADDR*)&clientAddr, &clientAddrSize);
    int clientID = addClient(clientSocket, clientAddr);
    HANDLE hThread = (HANDLE)_beginthreadex(NULL, 0, handleClient, &clients[clientID], 0, NULL);
    // ...existing code...
}
```

- **消息广播**  
  `broadcastMessage`函数遍历所有活跃客户端，将消息发送给除发送者外的所有人，实现聊天室功能。

```c
void broadcastMessage(char* message, int senderID) {
    EnterCriticalSection(&clientsLock);
    for (int i = 0; i < MAX_CLIENTS; i++) {
        if (clients[i].active && i != senderID) {
            send(clients[i].socket, message, strlen(message), 0);
        }
    }
    LeaveCriticalSection(&clientsLock);
}
```

- **用户名设置与提示**  
  客户端连接后，服务器主动发送欢迎消息和用户名输入提示，收到用户名后广播加入信息。

```c
// 发送欢迎消息
sprintf(welcomeMsg, "欢迎连接到TCP聊天服务器！您的ID是: %d\n请输入您的用户名: ", client->id);
send(client->socket, welcomeMsg, strlen(welcomeMsg), 0);

// 接收用户名
bytesReceived = recv(client->socket, buffer, BUFFER_SIZE - 1, 0);
if (bytesReceived > 0) {
    buffer[bytesReceived] = '\0';
    strcpy(client->username, buffer);
    // ...existing code...
}
```

- **断开与清理**  
  客户端退出或异常断开时，服务器清理资源并广播离开消息。

```c
void removeClient(int clientID) {
    EnterCriticalSection(&clientsLock);
    if (clientID >= 0 && clientID < MAX_CLIENTS && clients[clientID].active) {
        closesocket(clients[clientID].socket);
        clients[clientID].active = 0;
        clientCount--;
        printf("客户端 %s (ID=%d) 已断开连接\n", clients[clientID].username, clients[clientID].id);
    }
    LeaveCriticalSection(&clientsLock);
}
```

### 2. 客户端（tcp_client.c/extend.c的客户端部分）

- **连接与初始化**  
  客户端启动后连接服务器，成功后创建接收消息的独立线程。

```c
clientSocket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
connect(clientSocket, (SOCKADDR*)&serverAddr, sizeof(serverAddr));
// ...existing code...
HANDLE hReceiveThread = (HANDLE)_beginthreadex(NULL, 0, receiveMessages, NULL, 0, NULL);
```

- **消息收发**  
  主线程负责读取用户输入并发送至服务器，接收线程实时显示服务器广播的消息。

```c
while (running) {
    printf("输入消息 (输入 'quit' 退出): ");
    if (fgets(sendBuffer, sizeof(sendBuffer), stdin) != NULL) {
        // ...existing code...
        send(clientSocket, sendBuffer, strlen(sendBuffer), 0);
    }
}
```

- **接收消息线程**
```c
unsigned __stdcall receiveMessages(void* arg) {
    char buffer[BUFFER_SIZE];
    int bytesReceived;
    while (running) {
        bytesReceived = recv(clientSocket, buffer, BUFFER_SIZE - 1, 0);
        if (bytesReceived <= 0) break;
        buffer[bytesReceived] = '\0';
        printf("%s", buffer);
    }
    return 0;
}
```

- **退出机制**  
  用户输入"quit"或连接异常时，客户端安全退出并释放资源。

### 3. 主程序（extend.c）

- **模式选择与统一结构**  
  程序启动后，用户可选择运行服务器或客户端模式，便于统一管理和测试。

```c
printf("请选择运行模式:\n");
printf("1. 运行TCP服务器\n");
printf("2. 运行TCP客户端\n");
scanf("%d", &choice);
switch (choice) {
    case 1: runServer(); break;
    case 2: runClient(); break;
    // ...existing code...
}
```

通过上述核心代码实现，程序能够支持多客户端并发聊天、用户名管理、消息广播和异常处理，具备完整的TCP聊天室功能。

## 实验验证

### 测试场景
1. **单客户端连接**
   - 验证基本连接功能
   - 测试消息发送和接收

2. **多客户端连接**
   - 同时连接多个客户端
   - 验证消息广播功能

3. **异常处理**
   - 客户端异常断开
   - 服务器重启测试

### 网络数据包验证
1. 观察TCP三次握手过程
2. 分析数据传输过程
3. 监控连接断开过程
4. 验证多连接的数据流

## 实验扩展建议

1. **增加文件传输功能**
2. **实现私聊功能**
3. **添加用户认证**
4. **支持表情和文件分享**
5. **实现消息历史记录**

## 注意事项

1. **防火墙设置**
   - 确保端口8889未被防火墙阻塞
   - Windows Defender可能会询问网络访问权限

2. **网络配置**
   - 默认使用本地回环地址(127.0.0.1)
   - 跨网络通信需修改SERVER_IP常量

3. **编译要求**
   - 需要链接ws2_32库
   - 支持Windows Socket API

4. **运行顺序**
   - 必须先启动服务器
   - 再启动客户端进行连接

## 实验结果示例

### 服务器端输出
```
=== TCP聊天服务器 ===
服务器启动成功，监听端口 8889
等待客户端连接...

新客户端连接: ID=1, IP=127.0.0.1:12345
客户端 ID=1 设置用户名为: Alice
[Alice]: Hello everyone!
```

### 客户端输出
```
=== TCP聊天客户端 ===
连接到服务器 127.0.0.1:8889...
成功连接到服务器！

欢迎连接到TCP聊天服务器！您的ID是: 1
请输入您的用户名: Alice
用户名设置成功！开始聊天吧（输入 'quit' 退出）:
输入消息: Hello everyone!
```

通过本实验，学生可以深入理解TCP协议的工作原理，掌握socket编程技术，并通过Wireshark分析网络数据包，加深对网络通信的理解。