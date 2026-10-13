#include "Model.h"
#include <cstddef>
#include <cmath>

Model::Model() {}

Model::~Model() {
    if (EBO) glDeleteBuffers(1, &EBO);
    if (VBO) glDeleteBuffers(1, &VBO);
    if (VAO) glDeleteVertexArrays(1, &VAO);
}

Model::Model(Model&& other) noexcept {
    VAO = other.VAO; VBO = other.VBO; EBO = other.EBO; indexCount = other.indexCount;
    other.VAO = other.VBO = other.EBO = 0; other.indexCount = 0;
}

Model& Model::operator=(Model&& other) noexcept {
    if (this == &other) return *this;
    if (EBO) glDeleteBuffers(1, &EBO);
    if (VBO) glDeleteBuffers(1, &VBO);
    if (VAO) glDeleteVertexArrays(1, &VAO);
    VAO = other.VAO; VBO = other.VBO; EBO = other.EBO; indexCount = other.indexCount;
    other.VAO = other.VBO = other.EBO = 0; other.indexCount = 0;
    return *this;
}

void Model::setMesh(const std::vector<Vertex>& vertices, const std::vector<unsigned int>& indices) {
    if (!VAO) glGenVertexArrays(1, &VAO);
    if (!VBO) glGenBuffers(1, &VBO);
    if (!EBO) glGenBuffers(1, &EBO);

    glBindVertexArray(VAO);
    glBindBuffer(GL_ARRAY_BUFFER, VBO);
    glBufferData(GL_ARRAY_BUFFER, vertices.size() * sizeof(Vertex), vertices.data(), GL_STATIC_DRAW);

    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.size() * sizeof(unsigned int), indices.data(), GL_STATIC_DRAW);

    // layout(location = 0) position
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, sizeof(Vertex), (void*)offsetof(Vertex, position));
    // layout(location = 1) normal
    glEnableVertexAttribArray(1);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, sizeof(Vertex), (void*)offsetof(Vertex, normal));
    // layout(location = 2) texcoord
    glEnableVertexAttribArray(2);
    glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, sizeof(Vertex), (void*)offsetof(Vertex, texcoord));
    // layout(location = 3) faceId
    glEnableVertexAttribArray(3);
    glVertexAttribPointer(3, 1, GL_FLOAT, GL_FALSE, sizeof(Vertex), (void*)offsetof(Vertex, faceId));

    glBindVertexArray(0);

    indexCount = static_cast<GLsizei>(indices.size());
}

void Model::draw() const {
    glBindVertexArray(VAO);
    glDrawElements(GL_TRIANGLES, indexCount, GL_UNSIGNED_INT, nullptr);
    glBindVertexArray(0);
}

void Model::setStoneTableMesh(float topW, float topD, float topT,
                              float legW, float legD, float legH,
                              float baseW, float baseD, float baseT) {
    std::vector<Vertex> vertices;
    std::vector<unsigned int> indices;

    auto addFace = [&](glm::vec3 p0, glm::vec3 p1, glm::vec3 p2, glm::vec3 p3,
                       glm::vec3 n, glm::vec2 uv0, glm::vec2 uv1, glm::vec2 uv2, glm::vec2 uv3, float faceId) {
        unsigned int start = static_cast<unsigned int>(vertices.size());
        vertices.push_back(Vertex{p0, n, uv0, faceId});
        vertices.push_back(Vertex{p1, n, uv1, faceId});
        vertices.push_back(Vertex{p2, n, uv2, faceId});
        vertices.push_back(Vertex{p3, n, uv3, faceId});
        // 两个三角形，确保法线朝外
        indices.push_back(start + 0); indices.push_back(start + 1); indices.push_back(start + 2);
        indices.push_back(start + 0); indices.push_back(start + 2); indices.push_back(start + 3);
    };

    auto addBox = [&](glm::vec3 minP, glm::vec3 maxP, float topFaceId, float bottomFaceId, float sideFaceId) {
        // 顶面 (+Z)
        addFace({minP.x, minP.y, maxP.z}, {maxP.x, minP.y, maxP.z}, {maxP.x, maxP.y, maxP.z}, {minP.x, maxP.y, maxP.z},
                {0,0,1}, {0,0}, {1,0}, {1,1}, {0,1}, topFaceId);
        // 底面 (-Z)（UV随意）
        addFace({minP.x, maxP.y, minP.z}, {maxP.x, maxP.y, minP.z}, {maxP.x, minP.y, minP.z}, {minP.x, minP.y, minP.z},
                {0,0,-1}, {0,0}, {1,0}, {1,1}, {0,1}, bottomFaceId);
        // 前 (+Y)
        addFace({minP.x, maxP.y, minP.z}, {maxP.x, maxP.y, minP.z}, {maxP.x, maxP.y, maxP.z}, {minP.x, maxP.y, maxP.z},
                {0,1,0}, {0,0}, {1,0}, {1,1}, {0,1}, sideFaceId);
        // 后 (-Y)
        addFace({minP.x, minP.y, maxP.z}, {maxP.x, minP.y, maxP.z}, {maxP.x, minP.y, minP.z}, {minP.x, minP.y, minP.z},
                {0,-1,0}, {0,0}, {1,0}, {1,1}, {0,1}, sideFaceId);
        // 右 (+X)
        addFace({maxP.x, minP.y, minP.z}, {maxP.x, maxP.y, minP.z}, {maxP.x, maxP.y, maxP.z}, {maxP.x, minP.y, maxP.z},
                {1,0,0}, {0,0}, {1,0}, {1,1}, {0,1}, sideFaceId);
        // 左 (-X)
        addFace({minP.x, minP.y, maxP.z}, {minP.x, maxP.y, maxP.z}, {minP.x, maxP.y, minP.z}, {minP.x, minP.y, minP.z},
                {-1,0,0}, {0,0}, {1,0}, {1,1}, {0,1}, sideFaceId);
    };

    // 台面：顶面位于 z=0，底面位于 z=-topT
    glm::vec3 topMin(-topW * 0.5f, -topD * 0.5f, -topT);
    glm::vec3 topMax(+topW * 0.5f, +topD * 0.5f, 0.0f);
    addBox(topMin, topMax, /*top*/1.0f, /*bottom*/2.0f, /*side*/0.0f);

    // 桌腿：居中，顶部与台面底面相接
    glm::vec3 legMin(-legW * 0.5f, -legD * 0.5f, -topT - legH);
    glm::vec3 legMax(+legW * 0.5f, +legD * 0.5f, -topT);
    addBox(legMin, legMax, /*top*/1.0f, /*bottom*/2.0f, /*side*/0.0f);

    // 底座：居中，位于桌腿底部下方
    glm::vec3 baseMin(-baseW * 0.5f, -baseD * 0.5f, -topT - legH - baseT);
    glm::vec3 baseMax(+baseW * 0.5f, +baseD * 0.5f, -topT - legH);
    addBox(baseMin, baseMax, /*top*/1.0f, /*bottom*/2.0f, /*side*/0.0f);

    setMesh(vertices, indices);
}

void Model::setStoneStoolMesh(float radius, float height, int segments,
                              float wobbleAmp, int wobbleFreq) {
    segments = std::max(segments, 16);
    wobbleAmp = std::max(0.0f, std::min(wobbleAmp, 0.25f));
    wobbleFreq = std::max(1, wobbleFreq);

    std::vector<Vertex> vertices;
    std::vector<unsigned int> indices;

    const float zTop = 0.0f;
    const float zBottom = -height;
    const float twoPi = 6.28318530718f;

    auto perturbedRadius = [&](float theta, float t01) {
        // 半径随角度与高度产生轻微起伏（非规整效果）
        float a = wobbleAmp * std::sin(theta * wobbleFreq) * (0.6f + 0.4f * std::sin(t01 * twoPi));
        float b = wobbleAmp * 0.5f * std::cos(theta * (wobbleFreq + 2)) * (0.5f + 0.5f * std::cos(t01 * twoPi * 0.5f));
        return radius * (1.0f + a + b);
    };

    // 顶面（faceId=1.0）
    unsigned int topCenterIndex = static_cast<unsigned int>(vertices.size());
    vertices.push_back(Vertex{{0,0,zTop}, {0,0,1}, {0.5f,0.5f}, 1.0f});
    for (int i = 0; i <= segments; ++i) {
        float th = (float)i / segments * twoPi;
        float r = perturbedRadius(th, 0.0f);
        float x = std::cos(th) * r;
        float y = std::sin(th) * r;
        glm::vec2 uv = {0.5f + 0.5f * (x / (radius * 1.2f)), 0.5f + 0.5f * (y / (radius * 1.2f))};
        vertices.push_back(Vertex{{x, y, zTop}, {0,0,1}, uv, 1.0f});
    }
    for (int i = 0; i < segments; ++i) {
        indices.push_back(topCenterIndex);
        indices.push_back(topCenterIndex + 1 + i);
        indices.push_back(topCenterIndex + 2 + i);
    }

    // 底面（faceId=2.0）
    unsigned int bottomCenterIndex = static_cast<unsigned int>(vertices.size());
    vertices.push_back(Vertex{{0,0,zBottom}, {0,0,-1}, {0.5f,0.5f}, 2.0f});
    for (int i = 0; i <= segments; ++i) {
        float th = (float)i / segments * twoPi;
        float r = perturbedRadius(th, 1.0f);
        float x = std::cos(th) * r;
        float y = std::sin(th) * r;
        glm::vec2 uv = {0.5f + 0.5f * (x / (radius * 1.2f)), 0.5f + 0.5f * (y / (radius * 1.2f))};
        vertices.push_back(Vertex{{x, y, zBottom}, {0,0,-1}, uv, 2.0f});
    }
    for (int i = 0; i < segments; ++i) {
        indices.push_back(bottomCenterIndex);
        indices.push_back(bottomCenterIndex + 2 + i);
        indices.push_back(bottomCenterIndex + 1 + i);
    }

    // 侧面（faceId=0.0），法线按圆柱近似
    unsigned int sideStart = static_cast<unsigned int>(vertices.size());
    const float tileU = 3.0f;  // 增强横向平铺，纹理更明显
    const float tileV = 2.0f;  // 增强纵向平铺
    for (int i = 0; i <= segments; ++i) {
        float u = (float)i / segments;
        float th = u * twoPi;

        float rTop = perturbedRadius(th, 0.0f);
        float rBot = perturbedRadius(th, 1.0f);

        float cx = std::cos(th), sy = std::sin(th);
        glm::vec3 nrm = glm::normalize(glm::vec3(cx, sy, 0.0f));

        vertices.push_back(Vertex{{rTop * cx, rTop * sy, zTop},    nrm, {u * tileU, 1.0f * tileV}, 0.0f});
        vertices.push_back(Vertex{{rBot * cx, rBot * sy, zBottom}, nrm, {u * tileU, 0.0f * tileV}, 0.0f});
    }
    for (int i = 0; i < segments; ++i) {
        unsigned int i0 = sideStart + i * 2;
        unsigned int i1 = sideStart + i * 2 + 1;
        unsigned int i2 = sideStart + (i + 1) * 2;
        unsigned int i3 = sideStart + (i + 1) * 2 + 1;
        indices.push_back(i0); indices.push_back(i1); indices.push_back(i2);
        indices.push_back(i1); indices.push_back(i3); indices.push_back(i2);
    }

    setMesh(vertices, indices);
}
