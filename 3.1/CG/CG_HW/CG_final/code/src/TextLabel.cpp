#include "TextLabel.h"
#include <vector>
#include <iostream>
#include <glm/gtc/type_ptr.hpp>

static GLuint compileShader(GLenum type, const char* src) {
    GLuint sh = glCreateShader(type);
    glShaderSource(sh, 1, &src, nullptr);
    glCompileShader(sh);
    GLint ok = 0; glGetShaderiv(sh, GL_COMPILE_STATUS, &ok);
    if (!ok) { char log[512]; glGetShaderInfoLog(sh, 512, nullptr, log); std::cerr << log << std::endl; }
    return sh;
}
static GLuint createProgram(const char* vs, const char* fs) {
    GLuint v = compileShader(GL_VERTEX_SHADER, vs);
    GLuint f = compileShader(GL_FRAGMENT_SHADER, fs);
    GLuint p = glCreateProgram(); glAttachShader(p, v); glAttachShader(p, f); glLinkProgram(p);
    GLint ok = 0; glGetProgramiv(p, GL_LINK_STATUS, &ok);
    if (!ok) { char log[512]; glGetProgramInfoLog(p, 512, nullptr, log); std::cerr << log << std::endl; }
    glDeleteShader(v); glDeleteShader(f); return p;
}

// 5x7 栅格字形，使用位图行（高位在左）
static const unsigned char GLYPH_R[7] = {0xF0,0x90,0xF0,0xA0,0x90,0x90,0x90};
static const unsigned char GLYPH_E[7] = {0xF0,0x80,0xF0,0x80,0xF0,0x00,0x00};
static const unsigned char GLYPH_D[7] = {0xE0,0x90,0x90,0x90,0xE0,0x00,0x00};
static const unsigned char GLYPH_W[7] = {0x90,0x90,0xA0,0xA0,0xF0,0x90,0x90};
static const unsigned char GLYPH_I[7] = {0xF0,0x20,0x20,0x20,0xF0,0x00,0x00};
static const unsigned char GLYPH_N[7] = {0x90,0x90,0xB0,0xD0,0x90,0x00,0x00};
static const unsigned char GLYPH_B[7] = {0xE0,0x90,0xE0,0x90,0xE0,0x00,0x00};
static const unsigned char GLYPH_L[7] = {0x80,0x80,0x80,0x80,0xF0,0x00,0x00};
static const unsigned char GLYPH_A[7] = {0x60,0x90,0xF0,0x90,0x90,0x00,0x00};
static const unsigned char GLYPH_C[7] = {0x70,0x80,0x80,0x80,0x70,0x00,0x00};
static const unsigned char GLYPH_K[7] = {0x90,0xA0,0xC0,0xA0,0x90,0x00,0x00};
static const unsigned char GLYPH_SPACE[7] = {0x00,0x00,0x00,0x00,0x00,0x00,0x00};

const unsigned char* TextLabel::glyph(char c) {
    switch(c){
        case 'R': return GLYPH_R; case 'E': return GLYPH_E; case 'D': return GLYPH_D;
        case 'W': return GLYPH_W; case 'I': return GLYPH_I; case 'N': return GLYPH_N;
        case 'B': return GLYPH_B; case 'L': return GLYPH_L; case 'A': return GLYPH_A;
        case 'C': return GLYPH_C; case 'K': return GLYPH_K; case ' ': return GLYPH_SPACE;
        default: return GLYPH_SPACE;
    }
}

void TextLabel::setText(const std::string& t) {
    text = t;
    rebuildMesh();
}

void TextLabel::rebuildMesh() {
    // 简单方块字：每字符宽 5，高 7，字符间距 1
    float cellW = 1.0f, cellH = 1.4f; // 像素宽高比
    float gap = 1.0f;
    std::vector<Vertex> v; std::vector<unsigned int> idx;
    unsigned int base = 0;
    float xCursor = 0.0f;
    for(char c : text) {
        const unsigned char* g = glyph(c);
        for (int row=0; row<7; ++row) {
            unsigned char bits = g[row];
            for (int col=0; col<5; ++col) {
                bool on = (bits & (0x80 >> col)) != 0;
                if (!on) continue;
                float x0 = xCursor + col * cellW;
                float y0 = (6-row) * cellH;
                float x1 = x0 + cellW;
                float y1 = y0 + cellH;
                // 顶面四角（z=0）
                v.push_back(Vertex{{x0,y0,0}, {0,0,1}, {0,0}, 1.0f});
                v.push_back(Vertex{{x1,y0,0}, {0,0,1}, {0,0}, 1.0f});
                v.push_back(Vertex{{x1,y1,0}, {0,0,1}, {0,0}, 1.0f});
                v.push_back(Vertex{{x0,y1,0}, {0,0,1}, {0,0}, 1.0f});
                idx.push_back(base+0); idx.push_back(base+1); idx.push_back(base+2);
                idx.push_back(base+0); idx.push_back(base+2); idx.push_back(base+3);
                base += 4;
            }
        }
        xCursor += 5 * cellW + gap;
    }
    model.setMesh(v, idx);

    if (!program) {
        const char* vs = R"(#version 330 core
        layout(location=0)in vec3 aPos; layout(location=1)in vec3 aNormal;
        layout(location=2)in vec2 aTex; layout(location=3)in float aFace;
        uniform mat4 uModel,uView,uProj;
        void main(){ gl_Position=uProj*uView*uModel*vec4(aPos,1.0); })";
        const char* fs = R"(#version 330 core
        out vec4 FragColor; uniform vec3 uColor;
        void main(){ FragColor=vec4(uColor,1.0); })";
        program = createProgram(vs, fs);
    }
}

void TextLabel::draw(const glm::mat4& view, const glm::mat4& proj) {
    if (!program) return;
    glUseProgram(program);
    glUniformMatrix4fv(glGetUniformLocation(program,"uModel"),1,GL_FALSE,glm::value_ptr(modelMatrix));
    glUniformMatrix4fv(glGetUniformLocation(program,"uView"),1,GL_FALSE,glm::value_ptr(view));
    glUniformMatrix4fv(glGetUniformLocation(program,"uProj"),1,GL_FALSE,glm::value_ptr(proj));
    glUniform3fv(glGetUniformLocation(program,"uColor"),1,glm::value_ptr(color));
    model.draw();
    glUseProgram(0);
}
