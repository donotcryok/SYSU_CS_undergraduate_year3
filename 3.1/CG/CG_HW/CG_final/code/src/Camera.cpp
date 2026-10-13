// 主要功能：
// - 实现3D相机
// - 处理鼠标视角控制
// - 键盘WASD移动
// - 生成视图和投影矩阵
#include "Camera.h"
#include <GLFW/glfw3.h>
#include <cmath>
// 新增：使用 std::max 需要该头
#include <algorithm>

void CameraController::init(GLFWwindow* window,
                            const glm::vec3& initPos,
                            float initYawRad,
                            float initPitchRad,
                            float fovDegIn,
                            float nearIn,
                            float farIn) {
    position = initPos;
    yaw = initYawRad;
    pitch = initPitchRad;
    fovDeg = fovDegIn;
    nearZ = nearIn;
    farZ = farIn;

    // 备份初始状态
    defaultPos = initPos;
    defaultYaw = initYawRad;
    defaultPitch = initPitchRad;

    glfwGetCursorPos(window, &lastCursorX, &lastCursorY);
}

void CameraController::update(GLFWwindow* window, float dt, int fbWidth, int fbHeight) {
    // ESC 退出
    if (glfwGetKey(window, GLFW_KEY_ESCAPE) == GLFW_PRESS) {
        glfwSetWindowShouldClose(window, GLFW_TRUE);
    }

    // 0: 复位初始视角
    if (glfwGetKey(window, GLFW_KEY_0) == GLFW_PRESS) {
        position = defaultPos;
        yaw = defaultYaw;
        pitch = defaultPitch;
    }

    // 移除 WASD 自由移动，改为 1/2/3/4 切换固定视角
    // 计算参考距离和高度
    float dist = std::max(boardW, boardH) * 2.0f;
    float height = dist * 0.8f;

    // 1: 红方视角 (位于 -Y 侧，看向 +Y)
    if (glfwGetKey(window, GLFW_KEY_1) == GLFW_PRESS) {
        position = focusPoint + glm::vec3(0.0f, -dist, height);
        // 设置朝向：看向棋盘中心
        glm::vec3 dir = glm::normalize(focusPoint - position);
        yaw = std::atan2(dir.y, dir.x);
        pitch = std::asin(dir.z);
    }
    // 2: 黑方视角 (位于 +Y 侧，看向 -Y)
    if (glfwGetKey(window, GLFW_KEY_2) == GLFW_PRESS) {
        position = focusPoint + glm::vec3(0.0f, dist, height);
        glm::vec3 dir = glm::normalize(focusPoint - position);
        yaw = std::atan2(dir.y, dir.x);
        pitch = std::asin(dir.z);
    }
    // 3: 侧面视角 (位于 +X 侧，看向 -X)
    if (glfwGetKey(window, GLFW_KEY_3) == GLFW_PRESS) {
        position = focusPoint + glm::vec3(dist, 0.0f, height);
        glm::vec3 dir = glm::normalize(focusPoint - position);
        yaw = std::atan2(dir.y, dir.x);
        pitch = std::asin(dir.z);
    }
    // 4: 顶部俯视 (正上方)
    if (glfwGetKey(window, GLFW_KEY_4) == GLFW_PRESS) {
        float aspect = (fbHeight > 0) ? (static_cast<float>(fbWidth) / static_cast<float>(fbHeight)) : 1.0f;
        float vfov = glm::radians(fovDeg);
        float t = std::tan(vfov * 0.5f);
        float reqH = std::max((boardH * 0.5f) / t, (boardW * 0.5f) / (t * aspect));
        position = focusPoint + glm::vec3(0.0f, 0.0f, reqH * 1.05f);
        yaw = glm::radians(90.0f); // 保持上方朝向一致
        pitch = glm::radians(-90.0f);
    }

    // 鼠标拖拽调整方向（左键）
    double curX, curY; glfwGetCursorPos(window, &curX, &curY);
    if (mouseLookEnabled && glfwGetMouseButton(window, GLFW_MOUSE_BUTTON_LEFT) == GLFW_PRESS) {
        if (!dragging) { dragging = true; lastCursorX = curX; lastCursorY = curY; }
        double dx = curX - lastCursorX;
        double dy = curY - lastCursorY;
        yaw   += static_cast<float>(dx) * mouseSens;
        pitch -= static_cast<float>(dy) * mouseSens;
        // 限制俯仰角，避免万向节死锁
        pitch = std::max(glm::radians(-89.0f), std::min(glm::radians(89.0f), pitch));
        lastCursorX = curX; lastCursorY = curY;
    } else {
        dragging = false;
        lastCursorX = curX; lastCursorY = curY;
    }

    // 生成矩阵
    float aspect = (fbHeight > 0) ? (static_cast<float>(fbWidth) / static_cast<float>(fbHeight)) : 1.0f;
    proj = glm::perspective(glm::radians(fovDeg), aspect, nearZ, farZ);

    // 当前向为 -Z 时，up=(0,0,1) 与前向共线，改用 up=(0,1,0)
    glm::vec3 frontDir = getFront();
    glm::vec3 up(0, 0, 1);
    if (std::abs(glm::dot(frontDir, up)) > 0.99f) up = glm::vec3(0, 1, 0);

    view = glm::lookAt(position, position + frontDir, up);
}

