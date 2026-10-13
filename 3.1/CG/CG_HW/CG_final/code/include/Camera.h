#pragma once
#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <glad/glad.h>

// 前向声明，避免在头文件中包含 GLFW
struct GLFWwindow;

class CameraController {
public:
    // 初始化：窗口、初始位置、初始 yaw/pitch（弧度）、FOV(度)、近远裁剪
    void init(GLFWwindow* window,
              const glm::vec3& initPos,
              float initYawRad,
              float initPitchRad,
              float fovDeg,
              float nearZ,
              float farZ);

    // 每帧更新：处理输入并更新视图/投影矩阵
    void update(GLFWwindow* window, float dt, int fbWidth, int fbHeight);

    // 获取矩阵
    const glm::mat4& getView() const { return view; }
    const glm::mat4& getProj() const { return proj; }

    // 新增：设置棋盘中心与尺寸（用于 Y 键快速切换预设视角）
    void setFocusArea(const glm::vec3& focus, float boardWidth, float boardHeight) {
        focusPoint = focus;
        boardW = boardWidth;
        boardH = boardHeight;
    }

    // 新增：启用/禁用鼠标视角拖拽
    void setMouseLookEnabled(bool enabled) { mouseLookEnabled = enabled; }
    bool isMouseLookEnabled() const { return mouseLookEnabled; }

private:
    // 状态
    glm::vec3 position{0.0f, 0.0f, 0.0f};
    float yaw = 0.0f;     // 弧度
    float pitch = 0.0f;   // 弧度

    // 初始状态备份
    glm::vec3 defaultPos{0.0f, 0.0f, 0.0f};
    float defaultYaw = 0.0f;
    float defaultPitch = 0.0f;

    // 参数
    float moveSpeed = 8.0f;
    float mouseSens = 0.0035f;
    float fovDeg = 32.0f;
    float nearZ = 0.05f;
    float farZ = 1000.0f;

    // 鼠标
    double lastCursorX = 0.0;
    double lastCursorY = 0.0;
    bool dragging = false;
    bool mouseLookEnabled = true; // 新增：是否允许鼠标拖拽视角

    // 焦点与棋盘尺寸（供 Y 键预设视角使用）
    glm::vec3 focusPoint{0.0f, 0.0f, 0.0f};
    float boardW = 18.0f;
    float boardH = 20.0f;

    // 矩阵
    glm::mat4 view{1.0f};
    glm::mat4 proj{1.0f};

    // 工具
    static float clampf(float v, float lo, float hi) {
        return v < lo ? lo : (v > hi ? hi : v);
    }
    glm::vec3 getFront() const {
        glm::vec3 f(std::cos(yaw) * std::cos(pitch),
                    std::sin(yaw) * std::cos(pitch),
                    std::sin(pitch));
        return glm::normalize(f);
    }
};
