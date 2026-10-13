#include "ChessGame.h"
#include <GLFW/glfw3.h>
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/type_ptr.hpp>
#include <iostream>
#include <cwchar>
#include <cmath> // 新增：用于 std::sin

// 纹理路径映射（与原 main 中一致）
// 修正后的 getPieceTexturePaths 实现，与头文件保持一致
std::pair<std::wstring, std::wstring> ChessGame::getPieceTexturePaths(bool isRed, const wchar_t* name) {
    std::wstring basePath = L"assets/textures/";
    std::wstring front;
    
    if (isRed) {
        if (wcscmp(name, L"车") == 0) front = basePath + L"红车.png";
        else if (wcscmp(name, L"马") == 0) front = basePath + L"红马.png";
        else if (wcscmp(name, L"相") == 0) front = basePath + L"红相.png";
        else if (wcscmp(name, L"士") == 0) front = basePath + L"红仕.png";
        else if (wcscmp(name, L"将") == 0 || wcscmp(name, L"帅") == 0) front = basePath + L"红帅.png";
        else if (wcscmp(name, L"炮") == 0) front = basePath + L"红炮.png";
        else if (wcscmp(name, L"兵") == 0) front = basePath + L"红兵.png";
    } else {
        if (wcscmp(name, L"车") == 0) front = basePath + L"黑车.png";
        else if (wcscmp(name, L"马") == 0) front = basePath + L"黑马.png";
        else if (wcscmp(name, L"相") == 0 || wcscmp(name, L"象") == 0) front = basePath + L"黑象.png";
        else if (wcscmp(name, L"士") == 0) front = basePath + L"黑士.png";
        else if (wcscmp(name, L"帅") == 0 || wcscmp(name, L"将") == 0) front = basePath + L"黑将.png";
        else if (wcscmp(name, L"炮") == 0) front = basePath + L"黑炮.png";
        else if (wcscmp(name, L"卒") == 0) front = basePath + L"黑卒.png";
    }
    
    std::wstring back = basePath + L"棋子背面.png";
    return {front, back};
}
void ChessGame::init(GLFWwindow* window, const glm::vec2& gridOriginIn, float cellXIn, float cellYIn, float zLiftIn) {
    origin = gridOriginIn;
    cellX = cellXIn;
    cellY = cellYIn;
    zLift = zLiftIn;
    pieces.clear();
    makeStartingPieces(window);
    hasWinner = false;
    selectedIndex = -1;
    turn = Side::Red;
    // 新增：提示点与胜利标签
    initMarkersAndLabels();
}

static GLuint markerProgram = 0;
static GLuint markerVAO = 0, markerVBO = 0, markerEBO = 0;
static GLsizei markerIndexCount = 0;

void ChessGame::initMarkersAndLabels() {
    // 蓝色光点着色器
    auto compileShader = [](GLenum type, const char* src) {
        GLuint s = glCreateShader(type);
        glShaderSource(s, 1, &src, nullptr);
        glCompileShader(s);
        GLint ok = 0; glGetShaderiv(s, GL_COMPILE_STATUS, &ok);
        if (!ok) { char log[512]; glGetShaderInfoLog(s, 512, nullptr, log); std::cerr << log << std::endl; }
        return s;
    };
    auto createProgram = [&](const char* vs, const char* fs) {
        GLuint v = compileShader(GL_VERTEX_SHADER, vs);
        GLuint f = compileShader(GL_FRAGMENT_SHADER, fs);
        GLuint p = glCreateProgram(); glAttachShader(p, v); glAttachShader(p, f); glLinkProgram(p);
        GLint ok = 0; glGetProgramiv(p, GL_LINK_STATUS, &ok);
        if (!ok) { char log[512]; glGetProgramInfoLog(p, 512, nullptr, log); std::cerr << log << std::endl; }
        glDeleteShader(v); glDeleteShader(f); return p;
    };
    const char* vs = R"(#version 330 core
    layout(location=0) in vec3 aPos;
    layout(location=1) in vec3 aNormal;
    layout(location=2) in vec2 aTex;
    layout(location=3) in float aFace;
    uniform mat4 uModel,uView,uProj;
    void main(){ gl_Position = uProj * uView * uModel * vec4(aPos,1.0); })";
    const char* fs = R"(#version 330 core
    out vec4 FragColor; uniform vec3 uColor;
    void main(){ FragColor = vec4(uColor, 0.95); })";
    markerProgram = createProgram(vs, fs);

    // 构建小圆盘（顶面朝上） -> 使用 VAO/VBO/EBO 管线，替代原 markerDisk
    std::vector<Vertex> vv; std::vector<unsigned int> ii;
    int seg = 32; float r = 1.0f;
    vv.push_back(Vertex{{0,0,0}, {0,0,1}, {0,0}, 1.0f});
    for (int i=0;i<=seg;++i){
        float a = (float)i/seg * 6.2831853f;
        vv.push_back(Vertex{{r*std::cos(a), r*std::sin(a), 0}, {0,0,1}, {0,0}, 1.0f});
    }
    for (int i=0;i<seg;++i){ ii.push_back(0); ii.push_back(1+i); ii.push_back(2+i); }
    markerIndexCount = static_cast<GLsizei>(ii.size());

    if (markerVAO == 0) {
        glGenVertexArrays(1, &markerVAO);
        glGenBuffers(1, &markerVBO);
        glGenBuffers(1, &markerEBO);
    }
    glBindVertexArray(markerVAO);
    glBindBuffer(GL_ARRAY_BUFFER, markerVBO);
    glBufferData(GL_ARRAY_BUFFER, vv.size() * sizeof(Vertex), vv.data(), GL_STATIC_DRAW);
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, markerEBO);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, ii.size() * sizeof(unsigned int), ii.data(), GL_STATIC_DRAW);
    // 仅启用位置属性（着色器只用 aPos）
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, sizeof(Vertex), (void*)0);
    glBindVertexArray(0);

    // 删除：胜利标签初始化，不再显示获胜文字
}

void ChessGame::setBoardHeight(float newZ) {
    zLift = newZ;
    // 刷新所有棋子的模型矩阵
    for (auto& p : pieces) {
        placePiece(p, p.file, p.rank);
    }
}

void ChessGame::makeStartingPieces(GLFWwindow* window) {
    auto add = [&](Side side, PieceType type, int file, int rank, const wchar_t* name, float rScale, float hScale) {
        float R = std::min(cellX, cellY) * rScale;
        float H = std::min(cellX, cellY) * hScale;
        ChessPiece mesh(R, H, 96);
        auto paths = getPieceTexturePaths(side == Side::Red, name);
        mesh.initRenderer(/*window*/nullptr, paths.first, paths.second);
        PieceInst p{std::move(mesh), side, type, file, rank, true};
        // 黑方棋子旋转 180°，使棋子文字朝向与黑方玩家一致
        if (side == Side::Black) {
            p.rotationZRad = glm::pi<float>();
        }
        placePiece(p, file, rank);
        pieces.push_back(std::move(p));
    };

    // 红方（底部，rank=0 为最底行）
    add(Side::Red, PieceType::Rook,   0, 0, L"车", 0.38f, 0.30f);
    add(Side::Red, PieceType::Knight, 1, 0, L"马", 0.38f, 0.30f);
    add(Side::Red, PieceType::Bishop, 2, 0, L"相", 0.38f, 0.30f);
    add(Side::Red, PieceType::Guard,  3, 0, L"士", 0.38f, 0.30f);
    add(Side::Red, PieceType::King,   4, 0, L"将", 0.38f, 0.30f);
    add(Side::Red, PieceType::Guard,  5, 0, L"士", 0.38f, 0.30f);
    add(Side::Red, PieceType::Bishop, 6, 0, L"相", 0.38f, 0.30f);
    add(Side::Red, PieceType::Knight, 7, 0, L"马", 0.38f, 0.30f);
    add(Side::Red, PieceType::Rook,   8, 0, L"车", 0.38f, 0.30f);
    add(Side::Red, PieceType::Cannon, 1, 2, L"炮", 0.38f, 0.30f);
    add(Side::Red, PieceType::Cannon, 7, 2, L"炮", 0.38f, 0.30f);
    add(Side::Red, PieceType::Pawn,   0, 3, L"兵", 0.38f, 0.30f);
    add(Side::Red, PieceType::Pawn,   2, 3, L"兵", 0.38f, 0.30f);
    add(Side::Red, PieceType::Pawn,   4, 3, L"兵", 0.38f, 0.30f);
    add(Side::Red, PieceType::Pawn,   6, 3, L"兵", 0.38f, 0.30f);
    add(Side::Red, PieceType::Pawn,   8, 3, L"兵", 0.38f, 0.30f);

    // 黑方（顶部，rank=9 为最顶行）
    add(Side::Black, PieceType::Rook,   0, 9, L"车", 0.38f, 0.30f);
    add(Side::Black, PieceType::Knight, 1, 9, L"马", 0.38f, 0.30f);
    add(Side::Black, PieceType::Bishop, 2, 9, L"相", 0.38f, 0.30f);
    add(Side::Black, PieceType::Guard,  3, 9, L"士", 0.38f, 0.30f);
    add(Side::Black, PieceType::King,   4, 9, L"帅", 0.38f, 0.30f);
    add(Side::Black, PieceType::Guard,  5, 9, L"士", 0.38f, 0.30f);
    add(Side::Black, PieceType::Bishop, 6, 9, L"相", 0.38f, 0.30f);
    add(Side::Black, PieceType::Knight, 7, 9, L"马", 0.38f, 0.30f);
    add(Side::Black, PieceType::Rook,   8, 9, L"车", 0.38f, 0.30f);
    add(Side::Black, PieceType::Cannon, 1, 7, L"炮", 0.38f, 0.30f);
    add(Side::Black, PieceType::Cannon, 7, 7, L"炮", 0.38f, 0.30f);
    add(Side::Black, PieceType::Pawn,   0, 6, L"卒", 0.38f, 0.30f);
    add(Side::Black, PieceType::Pawn,   2, 6, L"卒", 0.38f, 0.30f);
    add(Side::Black, PieceType::Pawn,   4, 6, L"卒", 0.38f, 0.30f);
    add(Side::Black, PieceType::Pawn,   6, 6, L"卒", 0.38f, 0.30f);
    add(Side::Black, PieceType::Pawn,   8, 6, L"卒", 0.38f, 0.30f);
}

glm::vec3 ChessGame::gridToWorld(int file, int rank) const {
    return glm::vec3(origin.x + file * cellX, origin.y + rank * cellY, zLift);
}

void ChessGame::placePiece(PieceInst& p, int file, int rank, bool animate) {
    glm::vec3 targetPos = gridToWorld(file, rank);

    if (animate) {
        // 【核心修复】不要用网格计算起点！直接问显卡(矩阵)棋子现在在哪里
        // 获取模型矩阵的第4列（平移分量），这就是棋子当前的视觉位置
        glm::vec3 currentVisualPos = glm::vec3(p.mesh.getModelMatrix()[3]);
        
        p.animStartPos = currentVisualPos; // 设定真实视觉起点
        p.animDestPos = targetPos;         // 设定目标
        p.isAnimating = true;              // 开启标记
        p.animTime = 0.0f;                 // 重置计时器
    } else {
        // 初始化或重置时，瞬间设置位置
        p.isAnimating = false;
        glm::mat4 model = glm::translate(glm::mat4(1.0f), targetPos) *
                          glm::rotate(glm::mat4(1.0f), p.rotationZRad, glm::vec3(0.0f, 0.0f, 1.0f));
        p.mesh.setModelMatrix(model);
    }

    // 更新逻辑坐标
    p.file = file;
    p.rank = rank;
}

bool ChessGame::isOccupied(int file, int rank, int& outIndex) const {
    for (int i = 0; i < (int)pieces.size(); ++i) {
        if (!pieces[i].alive) continue;
        if (pieces[i].file == file && pieces[i].rank == rank) { outIndex = i; return true; }
    }
    return false;
}

bool ChessGame::screenToGrid(GLFWwindow* window, const glm::mat4& view, const glm::mat4& proj, int& outFile, int& outRank) {
    double mx, my; glfwGetCursorPos(window, &mx, &my);
    int w, h; glfwGetFramebufferSize(window, &w, &h);

    // NDC
    float x = (float)((mx / w) * 2.0 - 1.0);
    float y = (float)(((h - my) / h) * 2.0 - 1.0);

    // 构建射线（zNear=-1, zFar=+1）
    glm::vec4 pNearNDC(x, y, -1.0f, 1.0f);
    glm::vec4 pFarNDC (x, y, +1.0f, 1.0f);
    glm::mat4 invVP = glm::inverse(proj * view);
    glm::vec4 pNearWorld = invVP * pNearNDC; pNearWorld /= pNearWorld.w;
    glm::vec4 pFarWorld  = invVP * pFarNDC;  pFarWorld  /= pFarWorld.w;

    glm::vec3 o = glm::vec3(pNearWorld);
    glm::vec3 d = glm::normalize(glm::vec3(pFarWorld - pNearWorld));

    // 与 z = zLift 平面交点
    if (std::abs(d.z) < 1e-5f) return false;
    float t = (zLift - o.z) / d.z;
    if (t < 0.0f) return false;
    glm::vec3 hit = o + d * t;

    // 转为棋盘格坐标
    int file = (int)std::round((hit.x - origin.x) / cellX);
    int rank = (int)std::round((hit.y - origin.y) / cellY);
    if (file < 0 || file > 8 || rank < 0 || rank > 9) return false;

    outFile = file; outRank = rank;
    return true;
}

bool ChessGame::canRookMove(const PieceInst& p, int toFile, int toRank) const {
    if (p.file != toFile && p.rank != toRank) return false;
    int df = (toFile - p.file) == 0 ? 0 : (toFile > p.file ? 1 : -1);
    int dr = (toRank - p.rank) == 0 ? 0 : (toRank > p.rank ? 1 : -1);
    int f = p.file + df, r = p.rank + dr;
    while (f != toFile || r != toRank) {
        int idx; if (isOccupied(f, r, idx)) return false;
        f += df; r += dr;
    }
    return true;
}

bool ChessGame::canKnightMove(const PieceInst& p, int toFile, int toRank) const {
    int df = toFile - p.file, dr = toRank - p.rank;
    if (!((std::abs(df) == 2 && std::abs(dr) == 1) || (std::abs(df) == 1 && std::abs(dr) == 2))) return false;
    // 别马腿
    int legF = p.file + (df > 0 ? 1 : (df < 0 ? -1 : 0));
    int legR = p.rank + (dr > 0 ? 1 : (dr < 0 ? -1 : 0));
    if (std::abs(df) == 2) legR = p.rank;
    if (std::abs(dr) == 2) legF = p.file;
    int idx; return !isOccupied(legF, legR, idx);
}

bool ChessGame::canBishopMove(const PieceInst& p, int toFile, int toRank) const {
    int df = toFile - p.file, dr = toRank - p.rank;
    if (std::abs(df) != 2 || std::abs(dr) != 2) return false;
    // 象不过河
    if (p.side == Side::Red && toRank > 4) return false;
    if (p.side == Side::Black && toRank < 5) return false;
    // 塞象眼
    int eyeF = p.file + (df > 0 ? 1 : -1);
    int eyeR = p.rank + (dr > 0 ? 1 : -1);
    int idx; return !isOccupied(eyeF, eyeR, idx);
}

bool ChessGame::canGuardMove(const PieceInst& p, int toFile, int toRank) const {
    int df = std::abs(toFile - p.file), dr = std::abs(toRank - p.rank);
    if (df != 1 || dr != 1) return false;
    // 九宫格限制
    if (p.side == Side::Red) {
        return (toFile >= 3 && toFile <= 5 && toRank >= 0 && toRank <= 2);
    } else {
        return (toFile >= 3 && toFile <= 5 && toRank >= 7 && toRank <= 9);
    }
}

bool ChessGame::canKingMove(const PieceInst& p, int toFile, int toRank) const {
    int df = std::abs(toFile - p.file), dr = std::abs(toRank - p.rank);
    if (!((df == 1 && dr == 0) || (df == 0 && dr == 1))) return false;
    // 九宫格限制
    if (p.side == Side::Red) {
        return (toFile >= 3 && toFile <= 5 && toRank >= 0 && toRank <= 2);
    } else {
        return (toFile >= 3 && toFile <= 5 && toRank >= 7 && toRank <= 9);
    }
}

bool ChessGame::canCannonMove(const PieceInst& p, int toFile, int toRank) const {
    if (p.file != toFile && p.rank != toRank) return false;
    int df = (toFile - p.file) == 0 ? 0 : (toFile > p.file ? 1 : -1);
    int dr = (toRank - p.rank) == 0 ? 0 : (toRank > p.rank ? 1 : -1);
    int f = p.file + df, r = p.rank + dr;
    int midCount = 0;
    while (f != toFile || r != toRank) {
        int idx; if (isOccupied(f, r, idx)) midCount++;
        f += df; r += dr;
    }
    int targetIdx;
    bool targetOccupied = isOccupied(toFile, toRank, targetIdx);
    if (!targetOccupied) {
        // 平走不能跳
        return midCount == 0;
    } else {
        // 吃子必须隔一个
        return midCount == 1 && pieces[targetIdx].side != p.side;
    }
}

bool ChessGame::canPawnMove(const PieceInst& p, int toFile, int toRank) const {
    int df = toFile - p.file, dr = toRank - p.rank;
    if (p.side == Side::Red) {
        if (dr == 1 && df == 0) return true; // 向上
        if (p.rank >= 5 && dr == 0 && std::abs(df) == 1) return true; // 过河后可横走
    } else {
        if (dr == -1 && df == 0) return true; // 向下
        if (p.rank <= 4 && dr == 0 && std::abs(df) == 1) return true; // 过河后可横走
    }
    return false;
}

bool ChessGame::canMove(const PieceInst& p, int toFile, int toRank) const {
    if (toFile < 0 || toFile > 8 || toRank < 0 || toRank > 9) return false;
    int targetIdx;
    if (isOccupied(toFile, toRank, targetIdx) && pieces[targetIdx].side == p.side) return false; // 不能吃己方
    switch (p.type) {
        case PieceType::Rook:   return canRookMove(p, toFile, toRank);
        case PieceType::Knight: return canKnightMove(p, toFile, toRank);
        case PieceType::Bishop: return canBishopMove(p, toFile, toRank);
        case PieceType::Guard:  return canGuardMove(p, toFile, toRank);
        case PieceType::King:   return canKingMove(p, toFile, toRank);
        case PieceType::Cannon: return canCannonMove(p, toFile, toRank);
        case PieceType::Pawn:   return canPawnMove(p, toFile, toRank);
        default: return false;
    }
}

void ChessGame::switchTurn() { turn = (turn == Side::Red) ? Side::Black : Side::Red; }

void ChessGame::computeHintMoves(const PieceInst& p) {
    hintMoves.clear();
    for (int f=0; f<=8; ++f) {
        for (int r=0; r<=9; ++r) {
            if (f==p.file && r==p.rank) continue;
            if (canMove(p, f, r)) hintMoves.emplace_back(f, r);
        }
    }
}

void ChessGame::update(GLFWwindow* window, const glm::mat4& view, const glm::mat4& proj, float dt) {
    // 动画更新
    for (auto& p : pieces) {
        if (p.isAnimating) {
            p.animTime += dt;
            float t = p.animTime / p.animDuration;
            if (t >= 1.0f) {
                t = 1.0f;
                p.isAnimating = false;
                glm::mat4 model = glm::translate(glm::mat4(1.0f), p.animDestPos) *
                                  glm::rotate(glm::mat4(1.0f), p.rotationZRad, glm::vec3(0.0f, 0.0f, 1.0f));
                p.mesh.setModelMatrix(model);
            } else {
                // 平滑插值 (SmoothStep)
                float smoothT = t * t * (3.0f - 2.0f * t);
                glm::vec3 currentPos = glm::mix(p.animStartPos, p.animDestPos, smoothT);
                glm::mat4 model = glm::translate(glm::mat4(1.0f), currentPos) *
                                  glm::rotate(glm::mat4(1.0f), p.rotationZRad, glm::vec3(0.0f, 0.0f, 1.0f));
                p.mesh.setModelMatrix(model);
            }
        }
    }

    // b：重置
    if (glfwGetKey(window, GLFW_KEY_B) == GLFW_PRESS) {
        reset(window);
        return;
    }
    if (!interactionEnabled) return;

    int lmb = glfwGetMouseButton(window, GLFW_MOUSE_BUTTON_LEFT);
    bool clicked = (prevLMB == GLFW_RELEASE && lmb == GLFW_PRESS);
    prevLMB = lmb;

    if (!clicked) return;
    if (hasWinner) return;

    int gFile, gRank;
    if (!screenToGrid(window, view, proj, gFile, gRank)) return;

    int idx;
    if (selectedIndex < 0) {
        // 选择当前阵营的棋子并生成提示点
        if (isOccupied(gFile, gRank, idx) && pieces[idx].side == turn && pieces[idx].alive) {
            selectedIndex = idx;
            computeHintMoves(pieces[selectedIndex]);
        }
    } else {
        // 尝试移动或吃子
        PieceInst& p = pieces[selectedIndex];
        if (!canMove(p, gFile, gRank)) {
            // 取消或重新选择
            if (isOccupied(gFile, gRank, idx) && pieces[idx].side == turn && pieces[idx].alive) {
                selectedIndex = idx;
                computeHintMoves(pieces[selectedIndex]);
            } else {
                selectedIndex = -1;
                hintMoves.clear();
            }
            return;
        }
        int targetIdx;
        bool occupied = isOccupied(gFile, gRank, targetIdx);
        if (occupied) {
            bool capturedKing = (pieces[targetIdx].type == PieceType::King);
            pieces[targetIdx].alive = false;
            // 修复：先把当前棋子移动到目标格
            placePiece(p, gFile, gRank, true);
            if (capturedKing) {
                // 吃掉将/帅后宣布胜利，并停止交互；不切换回合
                declareWinner(window, p.side);
                hintMoves.clear();
                selectedIndex = -1;
                return;
            }
        } else {
            // 空格正常移动
            placePiece(p, gFile, gRank, true);
        }
        selectedIndex = -1;
        hintMoves.clear();
        switchTurn();
    }
}

void ChessGame::render(const glm::mat4& view,
                       const glm::mat4& proj,
                       const glm::mat4& lightVP,
                       GLuint shadowMap,
                       const glm::vec3& lightDir,
                       const glm::vec3& lightColor,
                       float ambient,
                       const glm::vec2& shadowTexel) {
    // 渲染棋子
    for (int i = 0; i < (int)pieces.size(); ++i) {
        auto& p = pieces[i];
        if (!p.alive) continue;

        if (i == selectedIndex) {
            // 选中特效：悬浮 + 呼吸
            glm::mat4 originalModel = p.mesh.getModelMatrix();

            // 计算悬浮偏移：基础抬高 0.5 + 呼吸幅度 0.1 * sin(时间 * 4.0)
            float time = static_cast<float>(glfwGetTime());
            float hoverOffset = 0.5f + 0.1f * std::sin(time * 4.0f);

            // 应用偏移（临时修改矩阵）
            // 注意：这里是在现有模型矩阵基础上沿 Z 轴平移
            glm::mat4 hoverModel = glm::translate(originalModel, glm::vec3(0.0f, 0.0f, hoverOffset));
            p.mesh.setModelMatrix(hoverModel);

            // 渲染
            p.mesh.render(view, proj, lightVP, shadowMap, lightDir, lightColor, ambient, shadowTexel);

            // 立即恢复原始矩阵，防止位置永久改变
            p.mesh.setModelMatrix(originalModel);
        } else {
            // 普通渲染
            p.mesh.render(view, proj, lightVP, shadowMap, lightDir, lightColor, ambient, shadowTexel);
        }
    }

    // 渲染提示点（蓝色光点）
    if (!hintMoves.empty() && markerProgram) {
        // 置顶绘制：禁用深度测试，避免被棋子覆盖
        glDisable(GL_DEPTH_TEST);
        glUseProgram(markerProgram);
        GLint locM = glGetUniformLocation(markerProgram, "uModel");
        glUniformMatrix4fv(glGetUniformLocation(markerProgram, "uView"), 1, GL_FALSE, glm::value_ptr(view));
        glUniformMatrix4fv(glGetUniformLocation(markerProgram, "uProj"), 1, GL_FALSE, glm::value_ptr(proj));
        glUniform3f(glGetUniformLocation(markerProgram, "uColor"), 0.15f, 0.45f, 0.95f);
        float r = markerRadius * std::min(cellX, cellY);
        glBindVertexArray(markerVAO);
        for (auto& sq : hintMoves) {
            glm::vec3 pos = gridToWorld(sq.x, sq.y);
            glm::mat4 m = glm::translate(glm::mat4(1.0f), glm::vec3(pos.x, pos.y, zLift + 0.0015f))
                        * glm::scale(glm::mat4(1.0f), glm::vec3(r, r, 1.0f));
            glUniformMatrix4fv(locM, 1, GL_FALSE, glm::value_ptr(m));
            glDrawElements(GL_TRIANGLES, markerIndexCount, GL_UNSIGNED_INT, nullptr);
        }
        glBindVertexArray(0);
        glUseProgram(0);
        glEnable(GL_DEPTH_TEST);
    }
}

void ChessGame::renderShadow(GLuint depthProgram, const glm::mat4& lightVP) {
    if (!depthProgram) return;
    GLint locM = glGetUniformLocation(depthProgram, "uModel");
    GLint locVP = glGetUniformLocation(depthProgram, "uLightVP");
    glUniformMatrix4fv(locVP, 1, GL_FALSE, glm::value_ptr(lightVP));
    for (auto& p : pieces) {
        if (!p.alive) continue;
        glm::mat4 modelMat = p.mesh.getModelMatrix();
        glUniformMatrix4fv(locM, 1, GL_FALSE, glm::value_ptr(modelMat));
        p.mesh.getModel().draw();
    }
}

void ChessGame::declareWinner(GLFWwindow* window, Side s) {
    hasWinner = true; winner = s;
    (void)window;
}

void ChessGame::reset(GLFWwindow* window) {
    pieces.clear();
    makeStartingPieces(window);
    hasWinner = false;
    selectedIndex = -1;
    hintMoves.clear();
    turn = Side::Red;
    // 重新布局标签（避免缩放变化）
    initMarkersAndLabels(); // 仅用于提示点资源的重建
}