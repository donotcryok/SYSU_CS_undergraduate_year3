#pragma once
#include <vector>
#include <string>
#include <glm/glm.hpp>
#include <glad/glad.h>
#include "ChessPiece.h"
#include "Model.h"  // 新增：markerDisk 需要
#include "TextLabel.h"

struct GLFWwindow;

enum class Side { Red, Black };
enum class PieceType { Rook, Knight, Bishop, Guard, King, Cannon, Pawn };

struct PieceInst {
    ChessPiece mesh;     // 渲染网格
    Side side;           // 阵营
    PieceType type;      // 类型
    int file;            // 0..8
    int rank;            // 0..9
    bool alive;          // 是否在场

    // 新增：用于控制棋子朝向（绕 Z 轴旋转，单位：弧度；黑方旋转 180°）
    float rotationZRad = 0.0f;

    // 动画状态
    bool isAnimating = false;
    glm::vec3 animStartPos{0.0f};
    glm::vec3 animDestPos{0.0f};
    float animTime = 0.0f;
    const float animDuration = 2.0f; // 动画时长 0.3秒
};

class ChessGame {
public:
    // 初始化：窗口、棋盘网格原点与单元尺寸、棋子底面抬高 z（与 main 中一致）
    void init(GLFWwindow* window, const glm::vec2& gridOrigin, float cellX, float cellY, float zLift);

    // 每帧更新与渲染
    void update(GLFWwindow* window, const glm::mat4& view, const glm::mat4& proj, float dt);
    void render(const glm::mat4& view,
                const glm::mat4& proj,
                const glm::mat4& lightVP,
                GLuint shadowMap,
                const glm::vec3& lightDir,
                const glm::vec3& lightColor,
                float ambient,
                const glm::vec2& shadowTexel);

    // 阴影专用渲染
    void renderShadow(GLuint depthProgram, const glm::mat4& lightVP);

    // 启用/禁用对局交互（禁用时左键拖拽不处理落子）
    void enableInteraction(bool enable) { interactionEnabled = enable; }

    // 新增：设置棋盘高度
    void setBoardHeight(float newZ);

    // 重置棋局为起始位置
    void reset(GLFWwindow* window);

private:
    // 资源与状态
    std::vector<PieceInst> pieces;

    // 提示点资源（蓝色光点）
    GLuint markerProgram = 0;   // 新增
    Model  markerDisk;          // 新增
    float  markerRadius = 0.18f;// 新增（相对 cell 的比例）

    // 当前选中棋子的所有合法落点（棋盘格坐标）
    std::vector<glm::ivec2> hintMoves; // 新增

    // 胜利文字标签（渲染到棋盘表面）
    TextLabel redWinLabel;
    TextLabel blackWinLabel;

    // 布局参数
    glm::vec2 origin{0.0f, 0.0f};
    float cellX = 1.0f;
    float cellY = 1.0f;
    float zLift = 0.001f;

    Side turn = Side::Red;
    bool interactionEnabled = false;
    bool hasWinner = false;
    Side winner = Side::Red;

    // 输入边沿检测
    int prevLMB = GLFW_RELEASE;

    // 选择状态
    int selectedIndex = -1;

    // 工具与规则
    std::pair<std::wstring, std::wstring> getPieceTexturePaths(bool isRed, const wchar_t* name);
    void makeStartingPieces(GLFWwindow* window);
    void placePiece(PieceInst& p, int file, int rank, bool animate = false);
    glm::vec3 gridToWorld(int file, int rank) const;
    bool screenToGrid(GLFWwindow* window, const glm::mat4& view, const glm::mat4& proj, int& outFile, int& outRank);
    bool isOccupied(int file, int rank, int& outIndex) const;
    bool canMove(const PieceInst& p, int toFile, int toRank) const;
    bool canRookMove(const PieceInst& p, int toFile, int toRank) const;
    bool canKnightMove(const PieceInst& p, int toFile, int toRank) const;
    bool canBishopMove(const PieceInst& p, int toFile, int toRank) const;
    bool canGuardMove(const PieceInst& p, int toFile, int toRank) const;
    bool canKingMove(const PieceInst& p, int toFile, int toRank) const;
    bool canCannonMove(const PieceInst& p, int toFile, int toRank) const;
    bool canPawnMove(const PieceInst& p, int toFile, int toRank) const;
    void switchTurn();
    void declareWinner(GLFWwindow* window, Side s);

    // 新增：初始化提示点着色器与网格；初始化胜利标签
    void initMarkersAndLabels();
    // 新增：计算并保存当前选中棋子的合法落点
    void computeHintMoves(const PieceInst& p);
};
