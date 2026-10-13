// 主要功能：
// - 棋子模型和纹理
// - 棋子的位置、颜色、类型
// - 拖拽状态管理
// - 棋盘位置映射
// - 移动合法性检查

#include "ChessPiece.h"
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/type_ptr.hpp>
#include <cmath>
#include <iostream>
#include <cstring>

#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <wincodec.h>
#pragma comment(lib, "Windowscodecs.lib")
#endif

ChessPiece::ChessPiece(float radius, float height, int segments) {
    buildMesh(radius, height, segments);
}

ChessPiece::~ChessPiece() {
    if (program) glDeleteProgram(program);
    if (texFront) glDeleteTextures(1, &texFront);
    if (texBack) glDeleteTextures(1, &texBack);
}

// 显式移动构造
ChessPiece::ChessPiece(ChessPiece&& other) noexcept
    : model(std::move(other.model)),
      texFront(other.texFront),
      texBack(other.texBack),
      program(other.program),
      modelMatrix(other.modelMatrix) {
    other.texFront = 0;
    other.texBack = 0;
    other.program = 0;
    other.modelMatrix = glm::mat4(1.0f);
}

// 显式移动赋值
ChessPiece& ChessPiece::operator=(ChessPiece&& other) noexcept {
    if (this == &other) return *this;

    // 释放自身资源
    if (program) { glDeleteProgram(program); program = 0; }
    if (texFront) { glDeleteTextures(1, &texFront); texFront = 0; }
    if (texBack)  { glDeleteTextures(1, &texBack);  texBack  = 0; }

    // 移动成员
    model = std::move(other.model);
    texFront = other.texFront; other.texFront = 0;
    texBack  = other.texBack;  other.texBack  = 0;
    program  = other.program;  other.program  = 0;
    modelMatrix = other.modelMatrix;
    other.modelMatrix = glm::mat4(1.0f);

    return *this;
}

void ChessPiece::setTextures(GLuint frontTex, GLuint backTex) {
    texFront = frontTex;
    texBack = backTex;
}

GLuint ChessPiece::compileShader(GLenum type, const char* src) {
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

GLuint ChessPiece::createProgram(const char* vs, const char* fs) {
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

GLuint ChessPiece::loadTexture2D_WIC(const std::wstring& wpath, bool flipY) {
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

bool ChessPiece::initRenderer(GLFWwindow* /*window*/,
                              const std::wstring& frontPath,
                              const std::wstring& backPath) {
    // 着色器源码
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

uniform sampler2D uFrontTex;
uniform sampler2D uBackTex;
uniform sampler2D uShadowMap;
// 底色：贴图透明区域与侧面使用该颜色
uniform vec3 uBaseColor;
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
    float bias = max(0.0025 * (1.0 - dot(normalize(normal), normalize(-uLightDir))), 0.0015);
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
    if (vFace > 1.5) {
        vec4 c = texture(uBackTex, vTex);
        color = c.a < 0.5 ? vec4(uBaseColor, 1.0) : c;
    } else if (vFace > 0.5) {
        vec4 c = texture(uFrontTex, vTex);
        color = c.a < 0.5 ? vec4(uBaseColor, 1.0) : c;
    } else {
        color = vec4(uBaseColor, 1.0);
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

    // 允许空路径：仅初始化着色器
    if (!frontPath.empty()) {
        texFront = loadTexture2D_WIC(frontPath, /*flipY=*/true);
    }
    if (!backPath.empty()) {
        texBack  = loadTexture2D_WIC(backPath,  /*flipY=*/true);
    }
    if (!texFront || !texBack) {
        std::wcerr << L"提示: 纹理未加载或为空路径，后续可通过 setTextures 绑定。" << std::endl;
    }

    glUseProgram(program);
    glUniform1i(glGetUniformLocation(program, "uFrontTex"), 0);
    glUniform1i(glGetUniformLocation(program, "uBackTex"), 1);
    glUniform1i(glGetUniformLocation(program, "uShadowMap"), 3);
    // 设置统一底色（象牙色）
    glUniform3f(glGetUniformLocation(program, "uBaseColor"), 0.92f, 0.86f, 0.72f);
    glUseProgram(0);
    return true;
}

// 删除旋转更新接口
// void ChessPiece::update(GLFWwindow* window, float dt) { ... }

// 渲染：直接使用固定的 modelMatrix
void ChessPiece::render(const glm::mat4& view,
                        const glm::mat4& proj,
                        const glm::mat4& lightVP,
                        GLuint shadowMap,
                        const glm::vec3& lightDir,
                        const glm::vec3& lightColor,
                        float ambient,
                        const glm::vec2& shadowTexel) {
    if (!program) return;

    // 修正局部变量名，避免与成员 model 重名
    glm::mat4 modelM = modelMatrix;

    glUseProgram(program);
    glUniformMatrix4fv(glGetUniformLocation(program, "uModel"), 1, GL_FALSE, glm::value_ptr(modelM));
    glUniformMatrix4fv(glGetUniformLocation(program, "uView"), 1, GL_FALSE, glm::value_ptr(view));
    glUniformMatrix4fv(glGetUniformLocation(program, "uProj"), 1, GL_FALSE, glm::value_ptr(proj));
    glUniformMatrix4fv(glGetUniformLocation(program, "uLightVP"), 1, GL_FALSE, glm::value_ptr(lightVP));
    glUniform3fv(glGetUniformLocation(program, "uLightDir"), 1, glm::value_ptr(lightDir));
    glUniform3fv(glGetUniformLocation(program, "uLightColor"), 1, glm::value_ptr(lightColor));
    glUniform1f(glGetUniformLocation(program, "uAmbient"), ambient);
    glUniform2fv(glGetUniformLocation(program, "uShadowTexel"), 1, glm::value_ptr(shadowTexel));

    glActiveTexture(GL_TEXTURE0); glBindTexture(GL_TEXTURE_2D, texFront);
    glActiveTexture(GL_TEXTURE1); glBindTexture(GL_TEXTURE_2D, texBack);
    glActiveTexture(GL_TEXTURE3); glBindTexture(GL_TEXTURE_2D, shadowMap);

    this->model.draw();
    glUseProgram(0);
}

void ChessPiece::draw() const {
    // 保留旧接口：仅绘制网格（不设置着色器/纹理）
    model.draw();
}

void ChessPiece::buildMesh(float radius, float height, int segments) {
    std::vector<Vertex> vertices;
    std::vector<unsigned int> indices;

    segments = std::max(segments, 8);
    const float h = height;                  // 顶面高度
    const float zTop = h;                    // 顶面 z = h
    const float zBottom = 0.0f;              // 底面 z = 0
    const float twoPi = 6.28318530718f;

    // 顶面
    unsigned int topCenterIndex = static_cast<unsigned int>(vertices.size());
    vertices.push_back({ {0.0f, 0.0f, zTop}, {0.0f, 0.0f, 1.0f}, {0.5f, 0.5f}, 1.0f });
    for (int i = 0; i <= segments; ++i) {
        float a = (float)i / segments * twoPi;
        float x = std::cos(a) * radius;
        float y = std::sin(a) * radius;
        glm::vec2 uv = {0.5f + 0.5f * (x / radius), 0.5f + 0.5f * (y / radius)};
        vertices.push_back({ {x, y, zTop}, {0.0f, 0.0f, 1.0f}, uv, 1.0f });
    }
    for (int i = 0; i < segments; ++i) {
        indices.push_back(topCenterIndex);
        indices.push_back(topCenterIndex + 1 + i);
        indices.push_back(topCenterIndex + 2 + i);
    }

    // 底面
    unsigned int bottomCenterIndex = static_cast<unsigned int>(vertices.size());
    vertices.push_back({ {0.0f, 0.0f, zBottom}, {0.0f, 0.0f, -1.0f}, {0.5f, 0.5f}, 2.0f });
    for (int i = 0; i <= segments; ++i) {
        float a = (float)i / segments * twoPi;
        float x = std::cos(a) * radius;
        float y = std::sin(a) * radius;
        glm::vec2 uv = {0.5f + 0.5f * (x / radius), 0.5f + 0.5f * (y / radius)};
        vertices.push_back({ {x, y, zBottom}, {0.0f, 0.0f, -1.0f}, uv, 2.0f });
    }
    for (int i = 0; i < segments; ++i) {
        // 保证绕序与法线一致（底面朝 -Z）
        indices.push_back(bottomCenterIndex);
        indices.push_back(bottomCenterIndex + 2 + i);
        indices.push_back(bottomCenterIndex + 1 + i);
    }

    // 侧面
    unsigned int sideStart = static_cast<unsigned int>(vertices.size());
    for (int i = 0; i <= segments; ++i) {
        float a = (float)i / segments * twoPi;
        float cx = std::cos(a), sy = std::sin(a);
        glm::vec3 normal = {cx, sy, 0.0f};
        float u = (float)i / segments;
        vertices.push_back({ {radius * cx, radius * sy, zTop   }, normal, {u, 1.0f}, 0.0f });
        vertices.push_back({ {radius * cx, radius * sy, zBottom}, normal, {u, 0.0f}, 0.0f });
    }
    for (int i = 0; i < segments; ++i) {
        unsigned int i0 = sideStart + i * 2;
        unsigned int i1 = sideStart + i * 2 + 1;
        unsigned int i2 = sideStart + (i + 1) * 2;
        unsigned int i3 = sideStart + (i + 1) * 2 + 1;
        indices.push_back(i0); indices.push_back(i1); indices.push_back(i2);
        indices.push_back(i1); indices.push_back(i3); indices.push_back(i2);
    }

    model.setMesh(vertices, indices);
}
