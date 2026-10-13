#pragma once
#include "Model.h"
#include "Texture.h"
#include <glm/glm.hpp>
#include <glad/glad.h>
#include <string>

class ChessBoard {
public:
    ChessBoard();
    ~ChessBoard();

    // 初始化渲染并加载棋盘纹理（中文路径）
    bool initRenderer(const std::wstring& boardTexPath);
    void setModelMatrix(const glm::mat4& m) { modelMatrix = m; }

    // 裁剪纹理外框（几何仍为整板，UV 映射为内圈）
    void setUVCrop(const glm::vec2& minUV, const glm::vec2& maxUV) { uvMin = minUV; uvMax = maxUV; }

    // 设置棋盘物理尺寸（与 setModelMatrix 的缩放匹配）
    void setPhysicalSize(float innerW, float innerH);

    // 设置“棋盘内圈网格”的 UV 矩形（对应 9x10 交点的包围矩形）
    void setGridUVRect(const glm::vec2& minUV, const glm::vec2& maxUV);

    // 通过边距设置网格（保留旧接口）
    void setLogicalGrid(float innerW, float innerH, float padX, float padY);

    // 将网格坐标(0..8, 0..9)映射至世界坐标（zOffset 用于抬高棋子底面）
    glm::vec3 gridToWorld(int file, int rank, float zOffset = 0.0f) const;

    // 获取当前网格 cell 尺寸
    float getCellSizeX() const { return cellSizeX; }
    float getCellSizeY() const { return cellSizeY; }

    // 新增：设置棋盘厚度（对象空间单位，顶面保持在 z=0，底面在负方向）
    void setThickness(float t) { thickness = t; }

    void render(const glm::mat4& view,
                const glm::mat4& proj,
                const glm::mat4& lightVP,
                GLuint shadowMap,
                const glm::vec3& lightDir,
                const glm::vec3& lightColor,
                float ambient,
                const glm::vec2& shadowTexel);
    void renderShadow(GLuint depthProgram, const glm::mat4& lightVP);

private:
    // 构建有厚度的棋盘盒体
    void buildPlane(float width, float height, float zTop);

    static GLuint compileShader(GLenum type, const char* src);
    static GLuint createProgram(const char* vs, const char* fs);
    // 加载纹理（不再计算平均色）
    static GLuint loadTexture2D_WIC(const std::wstring& wpath, bool flipY, glm::vec3* avgColorOut = nullptr);

    void updateGridFromUV(); // 根据当前 UV 设置与物理尺寸更新网格参数

    Model model;
    GLuint program = 0;
    GLuint texBoard = 0;
    glm::mat4 modelMatrix{1.0f};

    // UV 裁剪区域（默认全图）
    glm::vec2 uvMin{0.0f, 0.0f};
    glm::vec2 uvMax{1.0f, 1.0f};

    // 网格对应的 UV 包围矩形（默认与裁剪一致）
    glm::vec2 gridUVMin{0.0f, 0.0f};
    glm::vec2 gridUVMax{1.0f, 1.0f};

    // 统一木色（侧面与底面使用）
    glm::vec3 boardSolidColor{0.78f, 0.63f, 0.42f}; // 固定木色

    // 逻辑网格（单位：世界坐标）
    float innerWidth = 18.0f;
    float innerHeight = 20.0f;
    float padX = 0.0f;
    float padY = 0.0f;
    float cellSizeX = 18.0f / 8.0f;
    float cellSizeY = 20.0f / 9.0f;
    glm::vec2 gridOrigin{-innerWidth * 0.5f, -innerHeight * 0.5f};

    // 新增：棋盘厚度（对象空间）
    float thickness = 0.8f;

public:
    // 新增：提供模型与矩阵访问给阴影通道
    const Model& getModel() const { return model; }
    const glm::mat4& getModelMatrix() const { return modelMatrix; }
};
