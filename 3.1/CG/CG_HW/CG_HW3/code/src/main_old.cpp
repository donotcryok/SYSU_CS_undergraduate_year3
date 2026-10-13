#include "imgui.h"
#include "imgui_impl_glfw.h"
#include "imgui_impl_opengl3.h"
#include <GLFW/glfw3.h>
#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <vector>
#include <algorithm>
#include <iostream>
#include <cmath>

// 画布尺寸
const int CANVAS_WIDTH = 800;
const int CANVAS_HEIGHT = 600;

// 像素缓冲区
std::vector<unsigned char> pixelBuffer(CANVAS_WIDTH * CANVAS_HEIGHT * 3, 0);
// 深度缓冲区
std::vector<float> depthBuffer(CANVAS_WIDTH * CANVAS_HEIGHT, 1.0f);
// 枚举类型 
enum AlgorithmType { ALGO_DDA, ALGO_BRESENHAM };
enum ModelType { MODEL_TRIANGLE, MODEL_TETRAHEDRON, MODEL_CUBE };
enum ShadingType { SHADING_FLAT, SHADING_GOURAUD, SHADING_PHONG, SHADING_BLINN_PHONG };
// 全局状态
int currentAlgo = ALGO_DDA;
int currentModel = MODEL_TRIANGLE;
int currentShading = SHADING_FLAT;
float modelRotation = 0.0f;
// 交互控制
bool autoRotate = true;
float rotationSpeed = 1.0f;
bool useCustomColor = true;
glm::vec3 customColor = glm::vec3(1.0f, 0.5f, 0.2f);
// 光照参数
glm::vec3 lightPos = glm::vec3(0.0f, 0.0f, 3.0f);
glm::vec3 viewPos = glm::vec3(0.0f, 0.0f, 3.0f);
glm::vec3 lightColor = glm::vec3(1.0f, 1.0f, 1.0f);
float ambientStrength = 0.1f;
float specularStrength = 0.5f;
float shininess = 32.0f;
// 性能统计
float displayRenderTime = 0.0f;
double lastUpdateTime = 0.0;
double accumulatedTime = 0.0;
int frameCount = 0;
// 顶点结构
struct Vertex {
    glm::vec3 pos;   
    glm::vec3 normal; 
    glm::vec3 color; 
};
// 光栅化过程中的片元数据
struct Fragment {
    glm::vec3 worldPos;
    glm::vec3 normal;
    glm::vec3 color;
};

// 设置像素颜色的辅助函数
void SetPixel(int x, int y, float z, const glm::vec3& color) {
    if (x < 0 || x >= CANVAS_WIDTH || y < 0 || y >= CANVAS_HEIGHT) return;
    int index = y * CANVAS_WIDTH + x;
    // 深度测试 
    if (z < depthBuffer[index]) {
        depthBuffer[index] = z;
        int pixelIdx = index * 3;
        // 简单的颜色截断
        glm::vec3 c = glm::clamp(color, 0.0f, 1.0f);
        pixelBuffer[pixelIdx] = static_cast<unsigned char>(c.r * 255);
        pixelBuffer[pixelIdx + 1] = static_cast<unsigned char>(c.g * 255);
        pixelBuffer[pixelIdx + 2] = static_cast<unsigned char>(c.b * 255);
    }
}

// 清空缓冲区
void ClearBuffers(const glm::vec3& color) {
    unsigned char r = static_cast<unsigned char>(color.r * 255);
    unsigned char g = static_cast<unsigned char>(color.g * 255);
    unsigned char b = static_cast<unsigned char>(color.b * 255);
    for (size_t i = 0; i < pixelBuffer.size(); i += 3) {
        pixelBuffer[i] = r;
        pixelBuffer[i + 1] = g;
        pixelBuffer[i + 2] = b;
    }
    std::fill(depthBuffer.begin(), depthBuffer.end(), 1.0f);
}

// 光照计算函数
glm::vec3 CalculateLighting(glm::vec3 fragPos, glm::vec3 normal, glm::vec3 objectColor, bool isBlinn) {
    // 环境光
    glm::vec3 ambient = ambientStrength * lightColor;

    // 漫反射
    glm::vec3 norm = glm::normalize(normal);
    glm::vec3 lightDir = glm::normalize(lightPos - fragPos);
    float diff = std::max(glm::dot(norm, lightDir), 0.0f);
    glm::vec3 diffuse = diff * lightColor;

    // 镜面反射
    glm::vec3 viewDir = glm::normalize(viewPos - fragPos);
    float spec = 0.0f;
    if (isBlinn) {
        // Blinn-Phong
        glm::vec3 halfwayDir = glm::normalize(lightDir + viewDir);
        spec = std::pow(std::max(glm::dot(norm, halfwayDir), 0.0f), shininess);
    } else {
        // Phong
        glm::vec3 reflectDir = glm::reflect(-lightDir, norm);
        spec = std::pow(std::max(glm::dot(viewDir, reflectDir), 0.0f), shininess);
    }
    glm::vec3 specular = specularStrength * spec * lightColor;

    return (ambient + diffuse + specular) * objectColor;
}

// 属性结构体
struct Attribs {
    float z;
    glm::vec3 worldPos;
    glm::vec3 normal;
    glm::vec3 color; 

    // 线性插值
    static Attribs Lerp(const Attribs& a, const Attribs& b, float t) {
        Attribs res;
        res.z = a.z + (b.z - a.z) * t;
        res.worldPos = a.worldPos + (b.worldPos - a.worldPos) * t;
        res.normal = a.normal + (b.normal - a.normal) * t;
        res.color = a.color + (b.color - a.color) * t;
        return res;
    }
};

// 算法 1: DDA + Edge Walking + Shading
void RasterizeTriangle_DDA(
    glm::vec3 p0, glm::vec3 p1, glm::vec3 p2, // 屏幕坐标
    Attribs a0, Attribs a1, Attribs a2        // 属性
) {
    // 按 y 坐标排序
    if (p0.y > p1.y) { std::swap(p0, p1); std::swap(a0, a1); }
    if (p0.y > p2.y) { std::swap(p0, p2); std::swap(a0, a2); }
    if (p1.y > p2.y) { std::swap(p1, p2); std::swap(a1, a2); }

    int totalHeight = (int)(p2.y - p0.y);
    if (totalHeight == 0) return;

    // 左右边缘遍历器
    // 长边: p0 -> p2
    // 短边: p0 -> p1, 然后 p1 -> p2

    for (int i = 0; i < totalHeight; ++i) {
        int y = (int)p0.y + i;
        if (y < 0 || y >= CANVAS_HEIGHT) continue;

        // 计算长边的 t
        float t_long = (float)i / totalHeight;
        Attribs attr_long = Attribs::Lerp(a0, a2, t_long);
        float x_long = p0.x + (p2.x - p0.x) * t_long;

        // 计算短边的 t
        float t_short;
        Attribs attr_short;
        float x_short;

        int segmentHeight = (int)(p1.y - p0.y);
        if (i < segmentHeight) { // 上半部分
            t_short = (float)i / segmentHeight;
            attr_short = Attribs::Lerp(a0, a1, t_short);
            x_short = p0.x + (p1.x - p0.x) * t_short;
        } else { // 下半部分
            t_short = (float)(i - segmentHeight) / (totalHeight - segmentHeight);
            attr_short = Attribs::Lerp(a1, a2, t_short);
            x_short = p1.x + (p2.x - p1.x) * t_short;
        }

        // 确保 left 在左
        if (x_long > x_short) {
            std::swap(x_long, x_short);
            std::swap(attr_long, attr_short);
        }

        int xl = (int)x_long;
        int xr = (int)x_short;
        float spanWidth = x_short - x_long;

        for (int x = xl; x <= xr; x++) {
            if (x < 0 || x >= CANVAS_WIDTH) continue;
            
            float t_span = (spanWidth == 0) ? 0 : (float)(x - xl) / spanWidth;
            Attribs frag = Attribs::Lerp(attr_long, attr_short, t_span);

            glm::vec3 finalColor;
            if (currentShading == SHADING_FLAT) {
                finalColor = frag.color;
            } else if (currentShading == SHADING_GOURAUD) {
                finalColor = frag.color; // 已经在顶点计算并插值
            } else {
                // Phong 或 Blinn-Phong: 逐片元计算
                bool isBlinn = (currentShading == SHADING_BLINN_PHONG);
                glm::vec3 objColor = useCustomColor ? customColor : frag.color;
                finalColor = CalculateLighting(frag.worldPos, frag.normal, objColor, isBlinn);
            }

            SetPixel(x, y, frag.z, finalColor);
        }
    }
}

// 算法 2: Bresenham (整数运算模拟边缘) + Edge Walking + Shading
struct BresenhamWalker {
    int x, y, dx, dy, sx, err;
    
    void Init(glm::vec3 start, glm::vec3 end) {
        x = (int)start.x;
        y = (int)start.y;
        int x2 = (int)end.x;
        int y2 = (int)end.y;
        dx = std::abs(x2 - x);
        dy = std::abs(y2 - y); 
        sx = (x < x2) ? 1 : -1;
    }
    
    // 简单的整数 DDA 状态
    int rem;
    int totalY;
    
    void InitIntDDA(glm::vec3 start, glm::vec3 end) {
        x = (int)start.x;
        int x2 = (int)end.x;
        int y1 = (int)start.y;
        int y2 = (int)end.y;
        totalY = y2 - y1;
        dx = std::abs(x2 - x);
        sx = (x < x2) ? 1 : -1;
        rem = 0; 
    }

    void Step() {
        if (totalY == 0) return;
        int inc = dx / totalY;
        x += inc * sx;
        rem += (dx % totalY);
        if (rem >= totalY) {
            x += sx;
            rem -= totalY;
        }
    }
};

void RasterizeTriangle_Bresenham(
    glm::vec3 p0, glm::vec3 p1, glm::vec3 p2,
    Attribs a0, Attribs a1, Attribs a2
) {
    if (p0.y > p1.y) { std::swap(p0, p1); std::swap(a0, a1); }
    if (p0.y > p2.y) { std::swap(p0, p2); std::swap(a0, a2); }
    if (p1.y > p2.y) { std::swap(p1, p2); std::swap(a1, a2); }

    int totalHeight = (int)(p2.y - p0.y);
    if (totalHeight == 0) return;

    BresenhamWalker longEdge, shortEdge;
    longEdge.InitIntDDA(p0, p2);

    // 属性插值仍然需要浮点数 (因为属性是连续的)
    auto DrawSpan = [&](int y, int x1, int x2, float t_long, float t_short, bool isUpper) {
        Attribs attr_long = Attribs::Lerp(a0, a2, t_long);
        Attribs attr_short;
        if (isUpper) attr_short = Attribs::Lerp(a0, a1, t_short);
        else         attr_short = Attribs::Lerp(a1, a2, t_short);

        if (x1 > x2) { std::swap(x1, x2); std::swap(attr_long, attr_short); }
        
        float spanWidth = (float)(x2 - x1);
        for (int x = x1; x <= x2; x++) {
            if (x < 0 || x >= CANVAS_WIDTH) continue;
            float t = (spanWidth == 0) ? 0 : (float)(x - x1) / spanWidth;
            Attribs frag = Attribs::Lerp(attr_long, attr_short, t);

            glm::vec3 finalColor;
            if (currentShading == SHADING_FLAT) {
                finalColor = frag.color;
            } else if (currentShading == SHADING_GOURAUD) {
                finalColor = frag.color;
            } else {
                bool isBlinn = (currentShading == SHADING_BLINN_PHONG);
                glm::vec3 objColor = useCustomColor ? customColor : frag.color;
                finalColor = CalculateLighting(frag.worldPos, frag.normal, objColor, isBlinn);
            }
            SetPixel(x, y, frag.z, finalColor);
        }
    };

    // 上半部分
    int h1 = (int)(p1.y - p0.y);
    shortEdge.InitIntDDA(p0, p1);
    for (int i = 0; i < h1; i++) {
        int y = (int)p0.y + i;
        if (y >= 0 && y < CANVAS_HEIGHT) {
            float t_long = (float)i / totalHeight;
            float t_short = (float)i / h1;
            DrawSpan(y, longEdge.x, shortEdge.x, t_long, t_short, true);
        }
        longEdge.Step();
        shortEdge.Step();
    }

    // 下半部分
    int h2 = (int)(p2.y - p1.y);
    shortEdge.InitIntDDA(p1, p2); // 重置短边
    for (int i = 0; i <= h2; i++) { // <= 包含最后一行
        int y = (int)p1.y + i;
        if (y >= 0 && y < CANVAS_HEIGHT) {
            float t_long = (float)(h1 + i) / totalHeight;
            float t_short = (float)i / h2;
            DrawSpan(y, longEdge.x, shortEdge.x, t_long, t_short, false);
        }
        longEdge.Step();
        shortEdge.Step();
    }
}

// 模型数据生成
std::vector<Vertex> vertices;
std::vector<unsigned int> indices;

void CreateModel(ModelType type) {
    vertices.clear();
    indices.clear();

    auto addFace = [&](glm::vec3 a, glm::vec3 b, glm::vec3 c, glm::vec3 color) {
        glm::vec3 normal = glm::normalize(glm::cross(b - a, c - a));
        vertices.push_back({a, normal, color});
        vertices.push_back({b, normal, color});
        vertices.push_back({c, normal, color});
        unsigned int idx = (unsigned int)vertices.size();
        indices.push_back(idx - 3);
        indices.push_back(idx - 2);
        indices.push_back(idx - 1);
    };

    if (type == MODEL_TRIANGLE) {
        addFace({-0.5f, -0.5f, 0.0f}, {0.5f, -0.5f, 0.0f}, {0.0f, 0.5f, 0.0f}, {1,1,1});
        //手动设置颜色以演示插值
        vertices[0].color = {1,0,0}; vertices[1].color = {0,1,0}; vertices[2].color = {0,0,1};
    }
    else if (type == MODEL_TETRAHEDRON) {
        glm::vec3 top(0.0f, 0.5f, 0.0f);
        glm::vec3 v1(-0.5f, -0.5f, 0.5f);
        glm::vec3 v2(0.5f, -0.5f, 0.5f);
        glm::vec3 v3(0.0f, -0.5f, -0.5f);
        
        addFace(top, v2, v1, {1, 0, 0}); // Front
        addFace(top, v3, v2, {0, 1, 0}); // Right
        addFace(top, v1, v3, {0, 0, 1}); // Left
        addFace(v1, v2, v3, {1, 1, 0}); // Bottom
    }
    else if (type == MODEL_CUBE) {
        // 8 vertices
        glm::vec3 p[8] = {
            {-0.5f, -0.5f,  0.5f}, { 0.5f, -0.5f,  0.5f},
            { 0.5f,  0.5f,  0.5f}, {-0.5f,  0.5f,  0.5f},
            {-0.5f, -0.5f, -0.5f}, { 0.5f, -0.5f, -0.5f},
            { 0.5f,  0.5f, -0.5f}, {-0.5f,  0.5f, -0.5f}
        };
        // Front
        addFace(p[0], p[1], p[2], {1,0,0}); addFace(p[0], p[2], p[3], {1,0,0});
        // Back
        addFace(p[5], p[4], p[7], {0,1,0}); addFace(p[5], p[7], p[6], {0,1,0});
        // Left
        addFace(p[4], p[0], p[3], {0,0,1}); addFace(p[4], p[3], p[7], {0,0,1});
        // Right
        addFace(p[1], p[5], p[6], {1,1,0}); addFace(p[1], p[6], p[2], {1,1,0});
        // Top
        addFace(p[3], p[2], p[6], {0,1,1}); addFace(p[3], p[6], p[7], {0,1,1});
        // Bottom
        addFace(p[4], p[5], p[1], {1,0,1}); addFace(p[4], p[1], p[0], {1,0,1});
    }
}

int main(int, char**) {
    // 初始化窗口
    if (!glfwInit()) return 1;
    const char* glsl_version = "#version 130";
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 0);
    GLFWwindow* window = glfwCreateWindow(1280, 720, "CG HW2: Rasterization & Shading", NULL, NULL);
    if (window == NULL) return 1;
    glfwMakeContextCurrent(window);
    glfwSwapInterval(1);

    // 初始化 ImGui
    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    
    // 添加以下两行来放大字体和UI
    ImGuiIO& io = ImGui::GetIO();
    io.FontGlobalScale = 2.5f; 

    ImGui::StyleColorsDark();
    ImGui_ImplGlfw_InitForOpenGL(window, true);
    ImGui_ImplOpenGL3_Init(glsl_version);

    // 创建纹理
    GLuint textureID;
    glGenTextures(1, &textureID);
    glBindTexture(GL_TEXTURE_2D, textureID);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);

    // 初始化模型
    CreateModel((ModelType)currentModel);
    lastUpdateTime = glfwGetTime();

    while (!glfwWindowShouldClose(window)) {
        glfwPollEvents();

        ImGui_ImplOpenGL3_NewFrame();
        ImGui_ImplGlfw_NewFrame();
        ImGui::NewFrame();

        // 1. 清空缓冲区
        ClearBuffers(glm::vec3(0.1f, 0.1f, 0.1f));

        // 2. 更新变换矩阵
        if (autoRotate) {
            modelRotation += rotationSpeed * 0.01f;
        }
        
        glm::mat4 model = glm::rotate(glm::mat4(1.0f), modelRotation, glm::vec3(0.5f, 1.0f, 0.0f));
        model = glm::scale(model, glm::vec3(1.2f)); // 适当缩放模型以适应视图
        glm::mat4 view = glm::lookAt(viewPos, glm::vec3(0, 0, 0), glm::vec3(0, 1, 0));
        glm::mat4 projection = glm::perspective(glm::radians(45.0f), (float)CANVAS_WIDTH / CANVAS_HEIGHT, 0.1f, 100.0f);
        glm::mat4 mvp = projection * view * model;
        glm::mat4 modelInvTr = glm::transpose(glm::inverse(model)); // 法线变换矩阵

        // 3. 光栅化
        double startTime = glfwGetTime();
        
        glm::mat4 viewport = glm::mat4(1.0f);
        viewport = glm::translate(viewport, glm::vec3(CANVAS_WIDTH/2.0f, CANVAS_HEIGHT/2.0f, 0.0f));
        viewport = glm::scale(viewport, glm::vec3(CANVAS_WIDTH/2.0f, -CANVAS_HEIGHT/2.0f, 1.0f));

        for (size_t i = 0; i < indices.size(); i += 3) {
            Vertex v[3] = { vertices[indices[i]], vertices[indices[i+1]], vertices[indices[i+2]] };
            glm::vec3 p_screen[3];
            Attribs attribs[3];

            for(int j=0; j<3; ++j) {
                // 世界坐标
                glm::vec4 worldPos = model * glm::vec4(v[j].pos, 1.0f);
                attribs[j].worldPos = glm::vec3(worldPos);
                
                // 法向量 
                attribs[j].normal = glm::normalize(glm::vec3(modelInvTr * glm::vec4(v[j].normal, 0.0f)));
                
                // 屏幕坐标
                glm::vec4 clipPos = mvp * glm::vec4(v[j].pos, 1.0f);
                glm::vec3 ndc = glm::vec3(clipPos) / clipPos.w;
                p_screen[j] = glm::vec3(viewport * glm::vec4(ndc, 1.0f));
                
                // 深度
                attribs[j].z = ndc.z;

                // 颜色处理
                if (currentShading == SHADING_GOURAUD) {
                    // Gouraud: 顶点着色
                    glm::vec3 objColor = useCustomColor ? customColor : v[j].color;
                    attribs[j].color = CalculateLighting(attribs[j].worldPos, attribs[j].normal, objColor, false);
                } else if (currentShading == SHADING_FLAT) {
                    // Flat: 使用自定义颜色或顶点色
                    attribs[j].color = useCustomColor ? customColor : v[j].color;
                } else {
                    // Phong/Blinn: 传递基础颜色供插值
                    attribs[j].color = v[j].color;
                }
            }

            // 背面剔除 
            glm::vec3 n = glm::cross(p_screen[1] - p_screen[0], p_screen[2] - p_screen[0]);
            if (n.z >= 0) continue;
            if (currentAlgo == ALGO_DDA) {
                RasterizeTriangle_DDA(p_screen[0], p_screen[1], p_screen[2], attribs[0], attribs[1], attribs[2]);
            } else {
                RasterizeTriangle_Bresenham(p_screen[0], p_screen[1], p_screen[2], attribs[0], attribs[1], attribs[2]);
            }
        }

        double endTime = glfwGetTime();
        
        // 性能统计
        double frameTime = (endTime - startTime) * 1000.0;
        accumulatedTime += frameTime;
        frameCount++;
        if (glfwGetTime() - lastUpdateTime >= 3.0) {
            displayRenderTime = (float)(accumulatedTime / frameCount);
            accumulatedTime = 0; frameCount = 0; lastUpdateTime = glfwGetTime();
        }

        // 4. 更新纹理
        glBindTexture(GL_TEXTURE_2D, textureID);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, CANVAS_WIDTH, CANVAS_HEIGHT, 0, GL_RGB, GL_UNSIGNED_BYTE, pixelBuffer.data());

        // 5. UI
        ImGui::Begin("Control Panel");
        ImGui::Text("Avg Render Time: %.4f ms", displayRenderTime);
        ImGui::Text("Faces: %d", (int)indices.size() / 3);
        
        ImGui::Separator();
        ImGui::Text("Algorithm:");
        ImGui::RadioButton("DDA", &currentAlgo, ALGO_DDA); ImGui::SameLine();
        ImGui::RadioButton("Bresenham", &currentAlgo, ALGO_BRESENHAM);

        ImGui::Separator();
        ImGui::Text("Model:");
        if (ImGui::RadioButton("Triangle", &currentModel, MODEL_TRIANGLE)) CreateModel(MODEL_TRIANGLE); ImGui::SameLine();
        if (ImGui::RadioButton("Tetrahedron", &currentModel, MODEL_TETRAHEDRON)) CreateModel(MODEL_TETRAHEDRON); ImGui::SameLine();
        if (ImGui::RadioButton("Cube", &currentModel, MODEL_CUBE)) CreateModel(MODEL_CUBE);

        ImGui::Separator();
        ImGui::Text("Shading:");
        ImGui::RadioButton("Flat (Algo: Interp, Model: None)", &currentShading, SHADING_FLAT);
        ImGui::RadioButton("Gouraud (Algo: Vertex, Model: Phong)", &currentShading, SHADING_GOURAUD);
        ImGui::RadioButton("Phong (Algo: Pixel, Model: Phong)", &currentShading, SHADING_PHONG);
        ImGui::RadioButton("Blinn-Phong (Algo: Pixel, Model: Blinn-Phong)", &currentShading, SHADING_BLINN_PHONG);

        ImGui::Separator();
        ImGui::Text("Material & Light:");
        ImGui::Checkbox("Use Custom Color", &useCustomColor);
        if (useCustomColor) ImGui::ColorEdit3("Color", &customColor.x);
        ImGui::SliderFloat3("Light Pos", &lightPos.x, -5.0f, 5.0f);
        ImGui::SliderFloat("Shininess", &shininess, 2.0f, 256.0f);

        ImGui::Separator();
        ImGui::Text("Rotation:");
        ImGui::Checkbox("Auto", &autoRotate);
        if (autoRotate) ImGui::SliderFloat("Speed", &rotationSpeed, 0.0f, 5.0f);
        else ImGui::SliderFloat("Angle", &modelRotation, 0.0f, 6.28f);
        
        ImGui::End();

        ImGui::Begin("Viewport");
        ImGui::Image((void*)(intptr_t)textureID, ImVec2(CANVAS_WIDTH, CANVAS_HEIGHT));
        ImGui::End();

        ImGui::Render();
        int display_w, display_h;
        glfwGetFramebufferSize(window, &display_w, &display_h);
        glViewport(0, 0, display_w, display_h);
        glClearColor(0.45f, 0.55f, 0.60f, 1.00f);
        glClear(GL_COLOR_BUFFER_BIT);
        ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());

        glfwSwapBuffers(window);
    }

    ImGui_ImplOpenGL3_Shutdown();
    ImGui_ImplGlfw_Shutdown();
    ImGui::DestroyContext();
    glfwDestroyWindow(window);
    glfwTerminate();

    return 0;
}