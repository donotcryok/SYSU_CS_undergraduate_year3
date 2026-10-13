// 主要功能：
// - 棋盘模型和纹理
// - 管理棋子布局
// - 棋盘坐标系统
// - 判断格子位置
// - 渲染棋盘和格子
#include "ChessBoard.h"
#include <vector>
#include <iostream>
#include <glm/gtc/type_ptr.hpp>

#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <wincodec.h>
#pragma comment(lib, "Windowscodecs.lib")
#endif

ChessBoard::ChessBoard() {}
ChessBoard::~ChessBoard() {
    if (program) glDeleteProgram(program);
    if (texBoard) glDeleteTextures(1, &texBoard);
}

GLuint ChessBoard::compileShader(GLenum type, const char* src) {
    GLuint sh = glCreateShader(type);
    glShaderSource(sh, 1, &src, nullptr);
    glCompileShader(sh);
    GLint ok = 0; glGetShaderiv(sh, GL_COMPILE_STATUS, &ok);
    if (!ok) {
        char log[1024]; glGetShaderInfoLog(sh, 1024, nullptr, log);
        std::cerr << "Shader compile error: " << log << std::endl;
    }
    return sh;
}

GLuint ChessBoard::createProgram(const char* vs, const char* fs) {
    GLuint v = compileShader(GL_VERTEX_SHADER, vs);
    GLuint f = compileShader(GL_FRAGMENT_SHADER, fs);
    GLuint p = glCreateProgram();
    glAttachShader(p, v); glAttachShader(p, f);
    glLinkProgram(p);
    GLint ok = 0; glGetProgramiv(p, GL_LINK_STATUS, &ok);
    if (!ok) {
        char log[1024]; glGetProgramInfoLog(p, 1024, nullptr, log);
        std::cerr << "Program link error: " << log << std::endl;
    }
    glDeleteShader(v); glDeleteShader(f);
    return p;
}

GLuint ChessBoard::loadTexture2D_WIC(const std::wstring& wpath, bool flipY, glm::vec3* avgColorOut) {
#ifdef _WIN32
    HRESULT hr = CoInitializeEx(nullptr, COINIT_MULTITHREADED);
    bool didCoInit = SUCCEEDED(hr);
    IWICImagingFactory* factory = nullptr;
    IWICBitmapDecoder* decoder = nullptr;
    IWICBitmapFrameDecode* frame = nullptr;
    IWICFormatConverter* converter = nullptr;

    auto releaseAll = [&]() {
        if (converter) converter->Release();
        if (frame) frame->Release();
        if (decoder) decoder->Release();
        if (factory) factory->Release();
        if (didCoInit) CoUninitialize();
    };

    hr = CoCreateInstance(CLSID_WICImagingFactory, nullptr, CLSCTX_INPROC_SERVER, IID_PPV_ARGS(&factory));
    if (FAILED(hr)) { std::wcerr << L"WIC 工厂创建失败" << std::endl; releaseAll(); return 0; }

    hr = factory->CreateDecoderFromFilename(wpath.c_str(), nullptr, GENERIC_READ, WICDecodeMetadataCacheOnLoad, &decoder);
    if (FAILED(hr)) { std::wcerr << L"无法解码图片: " << wpath << std::endl; releaseAll(); return 0; }

    hr = decoder->GetFrame(0, &frame);
    if (FAILED(hr)) { std::wcerr << L"读取图片帧失败: " << wpath << std::endl; releaseAll(); return 0; }

    hr = factory->CreateFormatConverter(&converter);
    if (FAILED(hr)) { std::wcerr << L"创建格式转换器失败" << std::endl; releaseAll(); return 0; }

    hr = converter->Initialize(frame, GUID_WICPixelFormat32bppRGBA, WICBitmapDitherTypeNone, nullptr, 0.0, WICBitmapPaletteTypeCustom);
    if (FAILED(hr)) { std::wcerr << L"转换至 RGBA32 失败" << std::endl; releaseAll(); return 0; }

    UINT w = 0, h = 0;
    converter->GetSize(&w, &h);
    if (w == 0 || h == 0) { std::wcerr << L"图片尺寸无效" << std::endl; releaseAll(); return 0; }

    std::vector<unsigned char> rgba(w * h * 4);
    hr = converter->CopyPixels(nullptr, w * 4, static_cast<UINT>(rgba.size()), rgba.data());
    if (FAILED(hr)) { std::wcerr << L"复制像素失败" << std::endl; releaseAll(); return 0; }

    if (flipY) {
        const UINT stride = w * 4;
        std::vector<unsigned char> tmp(stride);
        for (UINT y = 0; y < h / 2; ++y) {
            unsigned char* rowTop = rgba.data() + y * stride;
            unsigned char* rowBottom = rgba.data() + (h - 1 - y) * stride;
            std::memcpy(tmp.data(), rowTop, stride);
            std::memcpy(rowTop, rowBottom, stride);
            std::memcpy(rowBottom, tmp.data(), stride);
        }
    }

    // 计算中心区域平均颜色（更接近正面主体色）
    if (avgColorOut) {
        size_t count = (size_t)w * (size_t)h;
        // 取中间 40%×40% 的区域
        UINT u0 = (UINT)(w * 0.30f), u1 = (UINT)(w * 0.70f);
        UINT v0 = (UINT)(h * 0.30f), v1 = (UINT)(h * 0.70f);
        double sumR = 0.0, sumG = 0.0, sumB = 0.0;
        size_t samples = 0;
        for (UINT y = v0; y < v1; ++y) {
            for (UINT x = u0; x < u1; ++x) {
                size_t i = (size_t)y * (size_t)w + (size_t)x;
                unsigned char r = rgba[i * 4 + 0];
                unsigned char g = rgba[i * 4 + 1];
                unsigned char b = rgba[i * 4 + 2];
                sumR += r; sumG += g; sumB += b;
                ++samples;
            }
        }
        if (samples > 0) {
            *avgColorOut = glm::vec3(
                (float)(sumR / (255.0 * samples)),
                (float)(sumG / (255.0 * samples)),
                (float)(sumB / (255.0 * samples))
            );
        }
    }

    GLuint tex = 0;
    glGenTextures(1, &tex);
    glBindTexture(GL_TEXTURE_2D, tex);
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, (GLsizei)w, (GLsizei)h, 0, GL_RGBA, GL_UNSIGNED_BYTE, rgba.data());
    glGenerateMipmap(GL_TEXTURE_2D);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);

    releaseAll();
    return tex;
#else
    return 0;
#endif
}

// 使用成员 thickness 构建 3D 盒体（顶面 zTop，底面 zBottom）
void ChessBoard::buildPlane(float width, float height, float zTop) {
    const float zBottom = zTop - thickness; // 使用成员 thickness

    struct V { glm::vec3 p; glm::vec3 n; glm::vec2 uv; float face; };
    std::vector<V> v;
    v.reserve(4 + 4 + 8); // 顶面+底面+侧面

    // 顶面（faceId=1.0）
    v.push_back({{-width*0.5f, -height*0.5f, zTop}, {0,0,1}, {uvMin.x, uvMin.y}, 1.0f});
    v.push_back({{+width*0.5f, -height*0.5f, zTop}, {0,0,1}, {uvMax.x, uvMin.y}, 1.0f});
    v.push_back({{+width*0.5f, +height*0.5f, zTop}, {0,0,1}, {uvMax.x, uvMax.y}, 1.0f});
    v.push_back({{-width*0.5f, +height*0.5f, zTop}, {0,0,1}, {uvMin.x, uvMax.y}, 1.0f});

    // 底面（faceId=2.0）
    v.push_back({{-width*0.5f, -height*0.5f, zBottom}, {0,0,-1}, {0,0}, 2.0f});
    v.push_back({{+width*0.5f, -height*0.5f, zBottom}, {0,0,-1}, {0,0}, 2.0f});
    v.push_back({{+width*0.5f, +height*0.5f, zBottom}, {0,0,-1}, {0,0}, 2.0f});
    v.push_back({{-width*0.5f, +height*0.5f, zBottom}, {0,0,-1}, {0,0}, 2.0f});

    // 侧面（faceId=0.0）
    // 左
    v.push_back({{-width*0.5f, -height*0.5f, zTop   }, {-1,0,0}, {0,0}, 0.0f});
    v.push_back({{-width*0.5f, -height*0.5f, zBottom}, {-1,0,0}, {0,0}, 0.0f});
    v.push_back({{-width*0.5f, +height*0.5f, zTop   }, {-1,0,0}, {0,0}, 0.0f});
    v.push_back({{-width*0.5f, +height*0.5f, zBottom}, {-1,0,0}, {0,0}, 0.0f});
    // 右
    v.push_back({{+width*0.5f, -height*0.5f, zTop   }, {+1,0,0}, {0,0}, 0.0f});
    v.push_back({{+width*0.5f, -height*0.5f, zBottom}, {+1,0,0}, {0,0}, 0.0f});
    v.push_back({{+width*0.5f, +height*0.5f, zTop   }, {+1,0,0}, {0,0}, 0.0f});
    v.push_back({{+width*0.5f, +height*0.5f, zBottom}, {+1,0,0}, {0,0}, 0.0f});
    // 下
    v.push_back({{-width*0.5f, -height*0.5f, zTop   }, {0,-1,0}, {0,0}, 0.0f});
    v.push_back({{-width*0.5f, -height*0.5f, zBottom}, {0,-1,0}, {0,0}, 0.0f});
    v.push_back({{+width*0.5f, -height*0.5f, zTop   }, {0,-1,0}, {0,0}, 0.0f});
    v.push_back({{+width*0.5f, -height*0.5f, zBottom}, {0,-1,0}, {0,0}, 0.0f});
    // 上
    v.push_back({{-width*0.5f, +height*0.5f, zTop   }, {0,+1,0}, {0,0}, 0.0f});
    v.push_back({{-width*0.5f, +height*0.5f, zBottom}, {0,+1,0}, {0,0}, 0.0f});
    v.push_back({{+width*0.5f, +height*0.5f, zTop   }, {0,+1,0}, {0,0}, 0.0f});
    v.push_back({{+width*0.5f, +height*0.5f, zBottom}, {0,0,0}, {0,0}, 0.0f});

    // 索引
    std::vector<unsigned int> idx;
    idx.reserve(6 * 2 + 6 * 4);

    // 顶面
    idx.insert(idx.end(), {0,1,2, 0,2,3});
    // 底面（逆序保证法线朝 -Z）
    idx.insert(idx.end(), {4,6,5, 4,7,6});

    // 侧面四边
    idx.insert(idx.end(), {8,9,10, 9,11,10});    // 左
    idx.insert(idx.end(), {12,13,14, 13,15,14}); // 右
    idx.insert(idx.end(), {16,17,18, 17,19,18}); // 下
    idx.insert(idx.end(), {20,21,22, 21,23,22}); // 上

    // 上传
    std::vector<Vertex> vv; vv.reserve(v.size());
    for (const auto& t : v) vv.push_back(Vertex{t.p, t.n, t.uv, t.face});
    model.setMesh(vv, idx);
}

void ChessBoard::setPhysicalSize(float innerW, float innerH) {
    innerWidth = innerW;
    innerHeight = innerH;
    updateGridFromUV();
}

void ChessBoard::setGridUVRect(const glm::vec2& minUV, const glm::vec2& maxUV) {
    gridUVMin = minUV;
    gridUVMax = maxUV;
    updateGridFromUV();
}

void ChessBoard::setLogicalGrid(float innerW, float innerH, float padXIn, float padYIn) {
    innerWidth = innerW;
    innerHeight = innerH;
    padX = padXIn;
    padY = padYIn;
    float effW = innerWidth - 2.0f * padX;
    float effH = innerHeight - 2.0f * padY;
    cellSizeX = effW / 8.0f;
    cellSizeY = effH / 9.0f;
    gridOrigin = glm::vec2(-innerWidth * 0.5f + padX, -innerHeight * 0.5f + padY);
}

void ChessBoard::updateGridFromUV() {
    // 将网格 UV 矩形映射到当前物理尺寸下的世界坐标
    float spanU = uvMax.x - uvMin.x;
    float spanV = uvMax.y - uvMin.y;
    if (spanU <= 0.0f || spanV <= 0.0f) return;

    // 左下角（几何坐标 -innerWidth/2, -innerHeight/2）
    float left   = -innerWidth  * 0.5f + (gridUVMin.x - uvMin.x) / spanU * innerWidth;
    float right  = -innerWidth  * 0.5f + (gridUVMax.x - uvMin.x) / spanU * innerWidth;
    float bottom = -innerHeight * 0.5f + (gridUVMin.y - uvMin.y) / spanV * innerHeight;
    float top    = -innerHeight * 0.5f + (gridUVMax.y - uvMin.y) / spanV * innerHeight;

    float effW = right - left;
    float effH = top - bottom;

    cellSizeX = effW / 8.0f;
    cellSizeY = effH / 9.0f;
    gridOrigin = glm::vec2(left, bottom);
}

glm::vec3 ChessBoard::gridToWorld(int file, int rank, float zOffset) const {
    float x = gridOrigin.x + file * cellSizeX;
    float y = gridOrigin.y + rank * cellSizeY;
    return glm::vec3(x, y, zOffset);
}

bool ChessBoard::initRenderer(const std::wstring& boardTexPath) {
    const char* vs = R"(#version 330 core
layout(location=0) in vec3 aPos;
layout(location=1) in vec3 aNormal;
layout(location=2) in vec2 aTex;
layout(location=3) in float aFace;

uniform mat4 uModel;
uniform mat4 uView;
uniform mat4 uProj;
uniform mat4 uLightVP;

out vec3 vNormal;
out vec2 vTex;
flat out float vFace;
out vec3 vWorldPos;

void main() {
    vec4 worldPos = uModel * vec4(aPos, 1.0);
    gl_Position = uProj * uView * worldPos;
    mat3 nrmMat = mat3(transpose(inverse(uModel)));
    vNormal = normalize(nrmMat * aNormal);
    vTex = aTex;
    vFace = aFace;
    vWorldPos = worldPos.xyz;
}
)";
    const char* fs = R"(#version 330 core
in vec3 vNormal;
in vec2 vTex;
flat in float vFace;
in vec3 vWorldPos;

uniform sampler2D uBoardTex;
uniform sampler2D uShadowMap;
uniform vec3 uSolidColor;
uniform vec3 uLightDir;
uniform vec3 uLightColor;
uniform float uAmbient;
uniform mat4 uLightVP;
uniform vec2 uShadowTexel;

out vec4 FragColor;

float computeShadow(vec3 worldPos, vec3 normal) {
    vec4 lp = uLightVP * vec4(worldPos, 1.0);
    vec3 proj = lp.xyz / lp.w;
    proj = proj * 0.5 + 0.5;
    if (proj.z > 1.0 || proj.x < 0.0 || proj.x > 1.0 || proj.y < 0.0 || proj.y > 1.0)
        return 0.0;
    float bias = max(0.003 * (1.0 - dot(normalize(normal), normalize(-uLightDir))), 0.0015);
    float shadow = 0.0;
    for (int x = -1; x <= 1; ++x) {
        for (int y = -1; y <= 1; ++y) {
            float p = texture(uShadowMap, proj.xy + vec2(x, y) * uShadowTexel).r;
            shadow += (proj.z - bias > p) ? 1.0 : 0.0;
        }
    }
    shadow /= 9.0;
    return shadow;
}

void main() {
    vec4 color;
    if (vFace > 0.5) {
        color = texture(uBoardTex, vTex);
    } else {
        color = vec4(uSolidColor, 1.0);
    }
    vec3 n = normalize(vNormal);
    vec3 L = normalize(-uLightDir);
    float ndl = max(dot(n, L), 0.0);
    float shadow = computeShadow(vWorldPos, n);
    vec3 ambient = color.rgb * uAmbient;
    vec3 diffuse = color.rgb * uLightColor * ndl * (1.0 - shadow);
    FragColor = vec4(ambient + diffuse, color.a);
}
)";
    program = createProgram(vs, fs);
    if (!program) return false;

    // 顶面 zTop=0，构建盒体
    buildPlane(1.0f, 1.0f, /*zTop=*/0.0f);

    // 加载棋盘纹理并取中心色作为木色
    texBoard = loadTexture2D_WIC(boardTexPath, /*flipY=*/true, &boardSolidColor);
    if (!texBoard) {
        std::wcerr << L"棋盘纹理加载失败。" << std::endl;
        return false;
    }
    glUseProgram(program);
    glUniform1i(glGetUniformLocation(program, "uBoardTex"), 0);
    glUniform3fv(glGetUniformLocation(program, "uSolidColor"), 1, glm::value_ptr(boardSolidColor));
    glUniform1i(glGetUniformLocation(program, "uShadowMap"), 3);
    glUseProgram(0);
    return true;
}

void ChessBoard::render(const glm::mat4& view,
                        const glm::mat4& proj,
                        const glm::mat4& lightVP,
                        GLuint shadowMap,
                        const glm::vec3& lightDir,
                        const glm::vec3& lightColor,
                        float ambient,
                        const glm::vec2& shadowTexel) {
    if (!program) return;

    glUseProgram(program);
    glUniformMatrix4fv(glGetUniformLocation(program, "uModel"), 1, GL_FALSE, glm::value_ptr(modelMatrix));
    glUniformMatrix4fv(glGetUniformLocation(program, "uView"), 1, GL_FALSE, glm::value_ptr(view));
    glUniformMatrix4fv(glGetUniformLocation(program, "uProj"), 1, GL_FALSE, glm::value_ptr(proj));
    glUniformMatrix4fv(glGetUniformLocation(program, "uLightVP"), 1, GL_FALSE, glm::value_ptr(lightVP));
    glUniform3fv(glGetUniformLocation(program, "uLightDir"), 1, glm::value_ptr(lightDir));
    glUniform3fv(glGetUniformLocation(program, "uLightColor"), 1, glm::value_ptr(lightColor));
    glUniform1f(glGetUniformLocation(program, "uAmbient"), ambient);
    glUniform2fv(glGetUniformLocation(program, "uShadowTexel"), 1, glm::value_ptr(shadowTexel));

    glActiveTexture(GL_TEXTURE0); glBindTexture(GL_TEXTURE_2D, texBoard);
    glActiveTexture(GL_TEXTURE3); glBindTexture(GL_TEXTURE_2D, shadowMap);
    model.draw();
    glUseProgram(0);
}

void ChessBoard::renderShadow(GLuint depthProgram, const glm::mat4& lightVP) {
    if (!depthProgram) return;
    glUniformMatrix4fv(glGetUniformLocation(depthProgram, "uModel"), 1, GL_FALSE, glm::value_ptr(modelMatrix));
    glUniformMatrix4fv(glGetUniformLocation(depthProgram, "uLightVP"), 1, GL_FALSE, glm::value_ptr(lightVP));
    model.draw();
}