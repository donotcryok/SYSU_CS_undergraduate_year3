#pragma once
#include "Model.h"
#include "Texture.h"
#include <glm/glm.hpp>
#include <glad/glad.h>
#include <vector>
#include <string> // 为 std::wstring

struct GLFWwindow; // 前向声明，避免在头文件中包含 GLFW

class ChessPiece {
  public:
    // radius: 半径, height: 厚度, segments: 圆周分段
    ChessPiece(float radius = 0.5f, float height = 0.2f, int segments = 64);
    ~ChessPiece();

    // 禁止拷贝，允许移动
    ChessPiece(const ChessPiece&) = delete;
    ChessPiece& operator=(const ChessPiece&) = delete;
    ChessPiece(ChessPiece&& other) noexcept;
    ChessPiece& operator=(ChessPiece&& other) noexcept;

    // 绑定正反面纹理(已创建好的 OpenGL 纹理ID)
    void setTextures(GLuint frontTex, GLuint backTex);

    // 初始化渲染（内部创建着色器并通过 WIC 加载纹理）
    // front/back 为中文路径（宽字符）
    bool initRenderer(GLFWwindow* window,
                      const std::wstring& frontPath,
                      const std::wstring& backPath);

    // 渲染（设置矩阵与必要 uniform）
    void render(const glm::mat4& view,
                const glm::mat4& proj,
                const glm::mat4& lightVP,
                GLuint shadowMap,
                const glm::vec3& lightDir,
                const glm::vec3& lightColor,
                float ambient,
                const glm::vec2& shadowTexel);

    // 模型矩阵
    void setModelMatrix(const glm::mat4& m) { modelMatrix = m; }
    const glm::mat4& getModelMatrix() const { return modelMatrix; }

    // 直接绘制底层网格（不设置着色器/纹理）
    void draw() const;

    // 获取底层模型（如需自定义绘制）
    const Model& getModel() const { return model; }

    // 新增：公开纹理加载工具，便于外部（如 main.cpp）复用 WIC 载图
    static GLuint loadTexture2D_WIC(const std::wstring& wpath, bool flipY);
  private:
    void buildMesh(float radius, float height, int segments);

    // 内部工具
    static GLuint compileShader(GLenum type, const char* src);
    static GLuint createProgram(const char* vs, const char* fs);

    Model model;
    GLuint texFront = 0;
    GLuint texBack = 0;
    GLuint program = 0;
    glm::mat4 modelMatrix{1.0f};
};
