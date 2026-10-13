// 主要功能：
// - 初始化GLFW和OpenGL
// - 初始化ImGui
// - 创建窗口
// - 加载着色器、纹理、模型
// - 主渲染循环
// - 处理鼠标键盘输入
// - 渲染场景
// - 实现棋子拖拽逻辑

#include <glad/glad.h>
#include <GLFW/glfw3.h>
#include <iostream>
#include <string>
#include <vector>
#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/type_ptr.hpp>
#include "ChessPiece.h"
#include "ChessBoard.h"
#include "Camera.h"
#include "ChessGame.h"
#include "Skybox.h"
#include <cmath>

int main() {
    if (!glfwInit()) return -1;

    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
#ifdef __APPLE__
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE);
#endif

    GLFWwindow* window = glfwCreateWindow(1280, 720, "Chinese Chess Piece - Preview", nullptr, nullptr);
    if (!window) { glfwTerminate(); return -1; }
    glfwMakeContextCurrent(window);
    glfwSwapInterval(1);

    if (!gladLoadGLLoader((GLADloadproc)glfwGetProcAddress)) {
        std::cerr << "Failed to init GLAD" << std::endl;
        return -1;
    }

    glEnable(GL_DEPTH_TEST);
    glDisable(GL_CULL_FACE);
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

    // 阴影贴图参数
    const unsigned int SHADOW_MAP_SIZE = 2048;
    const GLuint SHADOW_TEX_UNIT = 3;

    // 初始化天空盒
    Skybox skybox;
    if (!skybox.init(L"assets/textures/park_scene.jpg")) {
        std::wcerr << L"天空盒加载失败: assets/textures/park_scene.jpg" << std::endl;
    }

    // 棋盘：初始化与纹理
    ChessBoard board;
    board.setThickness(1.2f);
    std::wstring boardTex = L"assets/textures/象棋棋盘.png";
    if (!board.initRenderer(boardTex)) {
        std::wcerr << L"棋盘初始化失败。" << std::endl;
    }

    // 设定棋盘物理尺寸（与缩放保持一致）
    const float boardInnerW = 18.0f;
    const float boardInnerH = 20.0f;
    board.setModelMatrix(glm::scale(glm::mat4(1.0f), glm::vec3(boardInnerW, boardInnerH, 1.0f)));

    // 网格参数（根据纹理边界手动设定边距，确保边界格点对齐）
    // 修改：调整边距以匹配纹理。原先的边距较小导致网格计算偏大，棋子向外偏离。
    // 设定为 1.0f 后，有效区域为 16x18，格子尺寸为 2x2 (正方形)，通常能更好匹配标准棋盘贴图。
    const float padX = 1.0f; 
    const float padY = 1.0f; 

    // 计算有效区域与 cell 尺寸
    const float effW = boardInnerW - 2.0f * padX;
    const float effH = boardInnerH - 2.0f * padY;
    const float cellX = effW / 8.0f;
    const float cellY = effH / 9.0f;

    // 左下角原点（世界坐标）
    const glm::vec2 gridOrigin(-boardInnerW * 0.5f + padX, -boardInnerH * 0.5f + padY);

    // 棋盘网格中心（用于对齐桌子中心）
    const glm::vec2 boardCenterXY = gridOrigin + glm::vec2(4.0f * cellX, 4.5f * cellY);

    // 棋子尺寸与厚度（基于 cell）
    const float pieceR = std::min(cellX, cellY) * 0.38f;
    const float pieceH = std::min(cellX, cellY) * 0.30f;

    // 新增：底面抬高 z（供 ChessGame 使用）
    const float zLift = 0.001f;

    // 新增：石质桌子与两张凳子（及着色器/纹理）
    Model stoneTable;
    float tableTopW = boardInnerW * 1.40f;
    float tableTopD = boardInnerH * 1.40f;
    float tableTopT = 1.2f;
    float tableLegW = 6.0f,  tableLegD = 6.0f,  tableLegH = 10.0f;
    float tableBaseW = 12.0f, tableBaseD = 12.0f, tableBaseT = 2.0f;
    stoneTable.setStoneTableMesh(/*topW*/tableTopW, /*topD*/tableTopD, /*topT*/tableTopT,
                                 /*legW*/tableLegW, /*legD*/tableLegD, /*legH*/tableLegH,
                                 /*baseW*/tableBaseW, /*baseD*/tableBaseD, /*baseT*/tableBaseT);

    auto compileShader = [](GLenum type, const char* src) {
        GLuint sh = glCreateShader(type);
        glShaderSource(sh, 1, &src, nullptr);
        glCompileShader(sh);
        GLint ok = 0; glGetShaderiv(sh, GL_COMPILE_STATUS, &ok);
        if (!ok) { char log[1024]; glGetShaderInfoLog(sh, 1024, nullptr, log); std::cerr << log << std::endl; }
        return sh;
    };
    auto createProgram = [&](const char* vs, const char* fs) {
        GLuint v = compileShader(GL_VERTEX_SHADER, vs);
        GLuint f = compileShader(GL_FRAGMENT_SHADER, fs);
        GLuint p = glCreateProgram(); glAttachShader(p, v); glAttachShader(p, f); glLinkProgram(p);
        GLint ok = 0; glGetProgramiv(p, GL_LINK_STATUS, &ok);
        if (!ok) { char log[1024]; glGetProgramInfoLog(p, 1024, nullptr, log); std::cerr << log << std::endl; }
        glDeleteShader(v); glDeleteShader(f); return p;
    };
    const char* tableVS = R"(#version 330 core
layout(location=0) in vec3 aPos;
layout(location=1) in vec3 aNormal;
layout(location=2) in vec2 aTex;
layout(location=3) in float aFace;
uniform mat4 uModel, uView, uProj, uLightVP;
out vec3 vNormal; out vec2 vTex; out vec3 vWorld;
void main() {
    vec4 wp = uModel * vec4(aPos, 1.0);
    gl_Position = uProj * uView * wp;
    mat3 nrmMat = mat3(transpose(inverse(uModel)));
    vNormal = normalize(nrmMat * aNormal);
    vTex = aTex;
    vWorld = wp.xyz;
}
)";
    const char* tableFS = R"(#version 330 core
in vec3 vNormal; in vec2 vTex; in vec3 vWorld;
uniform sampler2D uTableTex;
uniform sampler2D uShadowMap;
uniform vec3 uLightDir;
uniform vec3 uLightColor;
uniform float uAmbient;
uniform mat4 uLightVP;
uniform vec2 uShadowTexel;
// 新增：用于区分“石桌石凳”（贴图）与“地面”（纯色）
uniform vec3 uSolidColor;
uniform float uUseSolidColor; // 0 使用纹理、1 使用纯色
out vec4 FragColor;

float computeShadow(vec3 worldPos, vec3 normal){
    vec4 lp = uLightVP * vec4(worldPos,1.0);
    vec3 proj = lp.xyz / lp.w;
    proj = proj * 0.5 + 0.5;
    if(proj.z > 1.0 || proj.x<0.0 || proj.x>1.0 || proj.y<0.0 || proj.y>1.0) return 0.0;
    float bias = max(0.0035 * (1.0 - dot(normalize(normal), normalize(-uLightDir))), 0.0015);
    float shadow = 0.0;
    for(int x=-1;x<=1;++x){
        for(int y=-1;y<=1;++y){
            float p = texture(uShadowMap, proj.xy + vec2(x,y)*uShadowTexel).r;
            shadow += (proj.z - bias > p) ? 1.0 : 0.0;
        }
    }
    return shadow/9.0;
}

void main() {
    vec3 texColor = texture(uTableTex, vTex).rgb;
    vec3 baseColor = mix(texColor, uSolidColor, uUseSolidColor);
    vec3 n = normalize(vNormal);
    vec3 L = normalize(-uLightDir);
    float ndl = max(dot(n, L), 0.0);
    float shadow = computeShadow(vWorld, n);
    vec3 ambient = baseColor * uAmbient;
    vec3 diffuse = baseColor * uLightColor * ndl * (1.0 - shadow);
    FragColor = vec4(ambient + diffuse, 1.0);
}
)";
    GLuint tableProgram = createProgram(tableVS, tableFS);
    // 石材纹理：桌面与石凳
    GLuint stoneTex = ChessPiece::loadTexture2D_WIC(
        L"assets/textures/石头石纹.jpg",
        /*flipY=*/true
    );
    // 草地纹理：用于地板（用户需提供 grass.jpg）
    // 为兼容不同工作目录，依次尝试多种常见相对路径
    GLuint grassTex = 0;
    const std::wstring grassCandidates[] = {
        // 首选：PNG 版本
        L"assets/textures/grass.png",
        L"../assets/textures/grass.png",
        L"../../assets/textures/grass.png",
        // 兼容：若仍旧存在 JPG，则也尝试
        L"assets/textures/grass.jpg",
        L"../assets/textures/grass.jpg",
        L"../../assets/textures/grass.jpg"
    };
    for (const auto& path : grassCandidates) {
        grassTex = ChessPiece::loadTexture2D_WIC(path, /*flipY=*/true);
        if (grassTex) {
            std::wcerr << L"[INFO] 草地纹理加载成功: " << path << std::endl;
            break;
        }
    }
    if (!grassTex) {
        std::wcerr << L"[WARN] 草地纹理 grass.jpg 加载失败，将使用纯色地面。" << std::endl;
    }
    // 为草地图设置包裹方式：单张完整图片覆盖整个地板（不平铺）
    if (grassTex) {
        glBindTexture(GL_TEXTURE_2D, grassTex);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    }
    glUseProgram(tableProgram);
    glUniform1i(glGetUniformLocation(tableProgram, "uTableTex"), 0);
    glUniform1i(glGetUniformLocation(tableProgram, "uShadowMap"), SHADOW_TEX_UNIT);
    // 默认：石桌石凳使用贴图
    glUniform1f(glGetUniformLocation(tableProgram, "uUseSolidColor"), 0.0f);
    glUseProgram(0);

    const float tableHeight = tableTopT + tableLegH + tableBaseT;
    const float stoolHeight = tableHeight * 0.5f;
    const float stoolRadius = 3.0f;
    Model stoolA, stoolB;
    stoolA.setStoneStoolMesh(stoolRadius, stoolHeight, /*segments*/64, /*wobbleAmp*/0.03f, /*wobbleFreq*/12);
    stoolB.setStoneStoolMesh(stoolRadius, stoolHeight, /*segments*/64, /*wobbleAmp*/0.03f, /*wobbleFreq*/16);

    // 新增：地面平面，接收阴影（贴草地图，尽量与天空盒地面融为一体）
    Model ground;
    {
        float z = 0.0f;
        std::vector<Vertex> v = {
            // 单张草地图完整覆盖整个地板：UV 范围 0..1
            {{-0.5f, -0.5f, z}, {0,0,1}, {0.0f, 0.0f}, 1.0f},
            {{ 0.5f, -0.5f, z}, {0,0,1}, {1.0f, 0.0f}, 1.0f},
            {{ 0.5f,  0.5f, z}, {0,0,1}, {1.0f, 1.0f}, 1.0f},
            {{-0.5f,  0.5f, z}, {0,0,1}, {0.0f, 1.0f}, 1.0f},
        };
        std::vector<unsigned int> idx = {0,1,2, 0,2,3};
        // 侧面/底面不需要，保持简单
        ground.setMesh(v, idx);
        // 使用 modelMatrix 控制缩放和平移
    }

    // 阴影贴图与深度着色器
    const char* depthVS = R"(#version 330 core
    layout(location=0) in vec3 aPos;
    uniform mat4 uModel;
    uniform mat4 uLightVP;
    void main(){ gl_Position = uLightVP * uModel * vec4(aPos,1.0); })";
    const char* depthFS = R"(#version 330 core
    void main() { })";
    GLuint depthProgram = createProgram(depthVS, depthFS);

    GLuint shadowFBO = 0, shadowTex = 0;
    {
        glGenFramebuffers(1, &shadowFBO);
        glGenTextures(1, &shadowTex);
        glBindTexture(GL_TEXTURE_2D, shadowTex);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT32F, SHADOW_MAP_SIZE, SHADOW_MAP_SIZE, 0, GL_DEPTH_COMPONENT, GL_FLOAT, nullptr);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER);
        float border[4] = {1.0f, 1.0f, 1.0f, 1.0f};
        glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, border);
        glBindFramebuffer(GL_FRAMEBUFFER, shadowFBO);
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, shadowTex, 0);
        glDrawBuffer(GL_NONE);
        glReadBuffer(GL_NONE);
        glBindFramebuffer(GL_FRAMEBUFFER, 0);
    }

    // 新增：相机控制器（恢复初始化）
    CameraController camera;
    {
        float radius = std::max(boardInnerW, boardInnerH) * 2.4f;
        glm::vec3 initPos(
            radius * std::cos(glm::radians(45.0f)),
            -radius * std::sin(glm::radians(45.0f)),
            boardInnerH * 1.15f
        );
        float initYaw   = std::atan2(-initPos.y, -initPos.x);
        float initPitch = glm::radians(-20.0f);
        camera.init(window, initPos, initYaw, initPitch, /*fovDeg*/32.0f, /*near*/0.05f, /*far*/1000.0f);
        camera.setFocusArea(glm::vec3(boardCenterXY.x, boardCenterXY.y, 0.0f), boardInnerW, boardInnerH);
    }

    // 象棋对局控制器
    ChessGame game;
    game.init(window, gridOrigin, cellX, cellY, zLift);

    // 新增：全局高度控制（初始位置稍微低一点）
    float globalHeight = -1.0f;

    // 时间步进
    double lastTime = glfwGetTime();

    // 新增：太阳光方位角（绕 Z 轴），初始值与原先 lightDir 大致一致
    float sunYaw = std::atan2(-0.75f, -0.6f);

    while (!glfwWindowShouldClose(window)) {
        int w, h; glfwGetFramebufferSize(window, &w, &h);
        // 计算 dt
        double now = glfwGetTime();
        float dt = static_cast<float>(now - lastTime);
        lastTime = now;

        // 【核心修复】防止卡顿或启动时 dt 过大导致动画瞬间播完
        if (dt > 0.05f) dt = 0.05f;

        // 高度调整按键
        if (glfwGetKey(window, GLFW_KEY_PAGE_UP) == GLFW_PRESS)   globalHeight += 2.0f * dt;
        if (glfwGetKey(window, GLFW_KEY_PAGE_DOWN) == GLFW_PRESS) globalHeight -= 2.0f * dt;

        // 应用高度到游戏逻辑 (保持 zLift 微小偏移)
        game.setBoardHeight(globalHeight + zLift);

        // 应用高度到棋盘模型 (位移 + 缩放)
        board.setModelMatrix(glm::translate(glm::mat4(1.0f), glm::vec3(0.0f, 0.0f, globalHeight)) * 
                             glm::scale(glm::mat4(1.0f), glm::vec3(boardInnerW, boardInnerH, 1.0f)));

        // 模式切换：y 启用对局（禁用相机鼠标视角），l 恢复相机鼠标视角（禁用对局）
        if (glfwGetKey(window, GLFW_KEY_Y) == GLFW_PRESS) {
            camera.setMouseLookEnabled(false);
            game.enableInteraction(true);
        }
        if (glfwGetKey(window, GLFW_KEY_L) == GLFW_PRESS) {
            camera.setMouseLookEnabled(true);
            game.enableInteraction(false);
        }

        // 新增：用 Q / E 键逆时针 / 顺时针旋转太阳光方向（绕 Z 轴）
        if (glfwGetKey(window, GLFW_KEY_Q) == GLFW_PRESS) {
            sunYaw += 0.6f * dt; // 逆时针
        }
        if (glfwGetKey(window, GLFW_KEY_E) == GLFW_PRESS) {
            sunYaw -= 0.6f * dt; // 顺时针
        }

        // 更新相机
        camera.update(window, dt, w, h);
        const glm::mat4& view = camera.getView();
        const glm::mat4& proj = camera.getProj();

        // 先更新棋局动画/交互，确保阴影使用最新姿态
        game.update(window, view, proj, dt);

        // 光源（模拟太阳方向，可绕 Z 轴旋转）
        glm::vec3 lightDir = glm::normalize(glm::vec3(std::cos(sunYaw), std::sin(sunYaw), -1.1f));
        glm::vec3 lightTarget(boardCenterXY.x, boardCenterXY.y, globalHeight);
        glm::vec3 lightPos = lightTarget - lightDir * 60.0f + glm::vec3(0.0f, 0.0f, 20.0f);
        glm::mat4 lightView = glm::lookAt(lightPos, lightTarget, glm::vec3(0,0,1));
        glm::mat4 lightProj = glm::ortho(-50.0f, 50.0f, -50.0f, 50.0f, 1.0f, 150.0f);
        glm::mat4 lightVP = lightProj * lightView;
        glm::vec2 shadowTexel(1.0f / SHADOW_MAP_SIZE, 1.0f / SHADOW_MAP_SIZE);
        glm::vec3 lightColor(1.0f, 0.97f, 0.92f);
        float ambientTerm = 0.25f;

        // 深度（阴影）渲染
        glViewport(0, 0, SHADOW_MAP_SIZE, SHADOW_MAP_SIZE);
        glBindFramebuffer(GL_FRAMEBUFFER, shadowFBO);
        glClear(GL_DEPTH_BUFFER_BIT);
        glUseProgram(depthProgram);
        GLint dpModel = glGetUniformLocation(depthProgram, "uModel");
        GLint dpVP = glGetUniformLocation(depthProgram, "uLightVP");
        glUniformMatrix4fv(dpVP, 1, GL_FALSE, glm::value_ptr(lightVP));

        auto renderDepth = [&](const Model& m, const glm::mat4& modelMat) {
            glUniformMatrix4fv(dpModel, 1, GL_FALSE, glm::value_ptr(modelMat));
            m.draw();
        };

        // 桌子与凳子
        // 修改：调整桌子高度以贴合棋盘底部 (棋盘厚度1.2，半厚0.6，原偏移2.2导致空隙)
        // 使用 -0.62f 略微向上嵌入一点，防止浮点误差导致的微小缝隙透光
        float tableTopZ = globalHeight - 0.62f;
        glm::mat4 tableModel = glm::translate(glm::mat4(1.0f), glm::vec3(0.0f, 0.0f, tableTopZ));
        renderDepth(stoneTable, tableModel);

        const float tableHeight = tableTopT + tableLegH + tableBaseT;
        const float stoolHeight = tableHeight * 0.5f;
        const float stoolRadius = 3.0f;
        
        // 计算地面高度：桌子顶面高度 - 桌子总高
        float groundZ = tableTopZ - tableHeight;
        
        // 凳子放置在地面上 (假设凳子原点在中心，需向上偏移半高)
        float stoolZ = groundZ + stoolHeight * 0.5f;

        const float sideOffsetY = (tableTopD * 0.5f) + stoolRadius + 1.2f;
        glm::mat4 stoolModelA = glm::translate(glm::mat4(1.0f), glm::vec3(0.0f, +sideOffsetY, stoolZ));
        glm::mat4 stoolModelB = glm::translate(glm::mat4(1.0f), glm::vec3(0.0f, -sideOffsetY, stoolZ));
        renderDepth(stoolA, stoolModelA);
        renderDepth(stoolB, stoolModelB);

        // 棋盘与棋子
        board.renderShadow(depthProgram, lightVP);
        game.renderShadow(depthProgram, lightVP);

        // 地面：在保证阴影完全落在地板上的前提下，适当缩小地板尺寸
        // 使用计算出的 groundZ 确保桌腿落地
        glm::mat4 groundModel = glm::translate(glm::mat4(1.0f), glm::vec3(0.0f, 0.0f, groundZ)) *
                                glm::scale(glm::mat4(1.0f), glm::vec3(80.0f, 80.0f, 1.0f));
        renderDepth(ground, groundModel);
        glUseProgram(0);

        glBindFramebuffer(GL_FRAMEBUFFER, 0);

        // 正常渲染通道
        glViewport(0, 0, w, h);
        glClearColor(0.15f, 0.18f, 0.20f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
        glActiveTexture(GL_TEXTURE0); // 默认回到 0
        glActiveTexture(GL_TEXTURE3); glBindTexture(GL_TEXTURE_2D, shadowTex);
        glActiveTexture(GL_TEXTURE0);

        // 渲染石质桌子（位于棋盘下方，中心与原点对齐）
        // 保持桌子在棋盘下方 2.2 单位
        glUseProgram(tableProgram);
        glUniformMatrix4fv(glGetUniformLocation(tableProgram, "uModel"), 1, GL_FALSE, glm::value_ptr(tableModel));
        glUniformMatrix4fv(glGetUniformLocation(tableProgram, "uView"), 1, GL_FALSE, glm::value_ptr(view));
        glUniformMatrix4fv(glGetUniformLocation(tableProgram, "uProj"), 1, GL_FALSE, glm::value_ptr(proj));
        glUniformMatrix4fv(glGetUniformLocation(tableProgram, "uLightVP"), 1, GL_FALSE, glm::value_ptr(lightVP));
        glUniform3fv(glGetUniformLocation(tableProgram, "uLightDir"), 1, glm::value_ptr(lightDir));
        glUniform3fv(glGetUniformLocation(tableProgram, "uLightColor"), 1, glm::value_ptr(lightColor));
        glUniform1f(glGetUniformLocation(tableProgram, "uAmbient"), ambientTerm);
        glUniform2fv(glGetUniformLocation(tableProgram, "uShadowTexel"), 1, glm::value_ptr(shadowTexel));
        // 石桌：使用石纹贴图颜色
        glUniform1f(glGetUniformLocation(tableProgram, "uUseSolidColor"), 0.0f);
        glActiveTexture(GL_TEXTURE0); glBindTexture(GL_TEXTURE_2D, stoneTex);
        glActiveTexture(GL_TEXTURE3); glBindTexture(GL_TEXTURE_2D, shadowTex);
        stoneTable.draw();
        glUseProgram(0);

        // 渲染两张石头凳子（以原点为中心，位于对弈两侧）
        glUseProgram(tableProgram);
        glUniformMatrix4fv(glGetUniformLocation(tableProgram, "uView"), 1, GL_FALSE, glm::value_ptr(view));
        glUniformMatrix4fv(glGetUniformLocation(tableProgram, "uProj"), 1, GL_FALSE, glm::value_ptr(proj));
        glUniformMatrix4fv(glGetUniformLocation(tableProgram, "uLightVP"), 1, GL_FALSE, glm::value_ptr(lightVP));
        glUniform3fv(glGetUniformLocation(tableProgram, "uLightDir"), 1, glm::value_ptr(lightDir));
        glUniform3fv(glGetUniformLocation(tableProgram, "uLightColor"), 1, glm::value_ptr(lightColor));
        glUniform1f(glGetUniformLocation(tableProgram, "uAmbient"), ambientTerm);
        glUniform2fv(glGetUniformLocation(tableProgram, "uShadowTexel"), 1, glm::value_ptr(shadowTexel));
        // 石桌石凳：使用贴图
        glUniform1f(glGetUniformLocation(tableProgram, "uUseSolidColor"), 0.0f);
        glActiveTexture(GL_TEXTURE0); glBindTexture(GL_TEXTURE_2D, stoneTex);
        glActiveTexture(GL_TEXTURE3); glBindTexture(GL_TEXTURE_2D, shadowTex);

        glUniformMatrix4fv(glGetUniformLocation(tableProgram, "uModel"), 1, GL_FALSE, glm::value_ptr(stoolModelA));
        stoolA.draw();

        glUniformMatrix4fv(glGetUniformLocation(tableProgram, "uModel"), 1, GL_FALSE, glm::value_ptr(stoolModelB));
        stoolB.draw();

        // 地面渲染：使用草地纹理（若加载失败则退回浅草色纯色）
        glm::vec3 groundColor(0.78f, 0.86f, 0.70f);
        glUniformMatrix4fv(glGetUniformLocation(tableProgram, "uModel"), 1, GL_FALSE, glm::value_ptr(groundModel));
        if (grassTex) {
            // 使用草地图：走纹理通道
            glActiveTexture(GL_TEXTURE0); glBindTexture(GL_TEXTURE_2D, grassTex);
            glUniform1f(glGetUniformLocation(tableProgram, "uUseSolidColor"), 0.0f);
        } else {
            // 兜底方案：使用浅草色纯色
            glUniform3fv(glGetUniformLocation(tableProgram, "uSolidColor"), 1, glm::value_ptr(groundColor));
            glUniform1f(glGetUniformLocation(tableProgram, "uUseSolidColor"), 1.0f);
        }
        ground.draw();

        glUseProgram(0);

        // 渲染棋盘
        board.render(view, proj, lightVP, shadowTex, lightDir, lightColor, ambientTerm, shadowTexel);

        // 渲染象棋对局（棋子）
        game.render(view, proj, lightVP, shadowTex, lightDir, lightColor, ambientTerm, shadowTexel);

        // 渲染天空盒
        skybox.render(view, proj);

        glfwSwapBuffers(window);
        glfwPollEvents();
    }

    glfwDestroyWindow(window);
    glfwTerminate();
    return 0;
}

