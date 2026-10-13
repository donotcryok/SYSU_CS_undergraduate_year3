#pragma once
#include <vector>
#include <glm/glm.hpp>
#include <GLFW/glfw3.h>    // 依赖 CMake 定义的 GLFW_INCLUDE_GLCOREARB
#include <glad/glad.h>

struct Vertex {
    glm::vec3 position;
    glm::vec3 normal;
    glm::vec2 texcoord;
    float faceId; // 0: side, 1: top, 2: bottom
};

class Model {
public:
    Model();
    ~Model();

    // 设置网格数据（一次性上传到GPU）
    void setMesh(const std::vector<Vertex>& vertices, const std::vector<unsigned int>& indices);

    // 绘制
    void draw() const;

    // 非拷贝，仅允许移动
    Model(const Model&) = delete;
    Model& operator=(const Model&) = delete;
    Model(Model&& other) noexcept;
    Model& operator=(Model&& other) noexcept;

    // 新增：构建石质象棋桌子网格
    // topW/topD: 台面宽/深（XY），topT: 台面厚度（Z，顶面在 z=0）
    // legW/legD/legH: 桌腿宽/深/高（矩形柱，位于台面下方居中）
    // baseW/baseD/baseT: 底座宽/深/厚（矩形台，位于桌腿下方居中）
    void setStoneTableMesh(float topW = 20.0f, float topD = 22.0f, float topT = 1.0f,
                           float legW = 4.0f, float legD = 4.0f, float legH = 9.0f,
                           float baseW = 8.0f, float baseD = 8.0f, float baseT = 1.2f);

    // 新增：构建“非规整圆柱形”石头凳子网格（顶部位于 z=0，底部 z=-height）
    // radius: 平均半径；height: 凳子高度；segments: 圆周分段；wobbleAmp: 半径起伏幅度(0~0.25)；wobbleFreq: 起伏频率
    void setStoneStoolMesh(float radius = 2.0f, float height = 5.6f, int segments = 48,
                           float wobbleAmp = 0.12f, int wobbleFreq = 5);

private:
    GLuint VAO = 0, VBO = 0, EBO = 0;
    GLsizei indexCount = 0;
};
