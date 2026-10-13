#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#endif

// 1. 包含标准 OpenGL 和 GLFW
#include <GL/gl.h>
#include <GLFW/glfw3.h>

// 2. 包含 ImGui
#include "imgui.h"
#include "backends/imgui_impl_glfw.h"
#include "backends/imgui_impl_opengl3.h"

#include <cmath>
#include <vector>
#include <iostream>
#include <string>

// =========================================================================
// [Mini-Loader] 手动定义现代 OpenGL (GL 1.5+) 所需的常量和函数指针
// =========================================================================

#define GL_ARRAY_BUFFER         0x8892
#define GL_ELEMENT_ARRAY_BUFFER 0x8893
#define GL_STATIC_DRAW          0x88E4
#define GL_FRAGMENT_SHADER      0x8B30
#define GL_VERTEX_SHADER        0x8B31
#define GL_COMPILE_STATUS       0x8B81
#define GL_LINK_STATUS          0x8B82
#define GL_INFO_LOG_LENGTH      0x8B84

typedef char GLchar;
typedef ptrdiff_t GLsizeiptr;

typedef void (APIENTRY* PFNGLGENBUFFERSPROC) (GLsizei n, GLuint* buffers);
typedef void (APIENTRY* PFNGLBINDBUFFERPROC) (GLenum target, GLuint buffer);
typedef void (APIENTRY* PFNGLBUFFERDATAPROC) (GLenum target, GLsizeiptr size, const void* data, GLenum usage);
typedef void (APIENTRY* PFNGLGENVERTEXARRAYSPROC) (GLsizei n, GLuint* arrays);
typedef void (APIENTRY* PFNGLBINDVERTEXARRAYPROC) (GLuint array);
typedef void (APIENTRY* PFNGLENABLEVERTEXATTRIBARRAYPROC) (GLuint index);
typedef void (APIENTRY* PFNGLVERTEXATTRIBPOINTERPROC) (GLuint index, GLint size, GLenum type, GLboolean normalized, GLsizei stride, const void* pointer);
typedef GLuint(APIENTRY* PFNGLCREATESHADERPROC) (GLenum type);
typedef void (APIENTRY* PFNGLSHADERSOURCEPROC) (GLuint shader, GLsizei count, const GLchar* const* string, const GLint* length);
typedef void (APIENTRY* PFNGLCOMPILESHADERPROC) (GLuint shader);
typedef void (APIENTRY* PFNGLGETSHADERIVPROC) (GLuint shader, GLenum pname, GLint* params);
typedef void (APIENTRY* PFNGLGETSHADERINFOLOGPROC) (GLuint shader, GLsizei bufSize, GLsizei* length, GLchar* infoLog);
typedef GLuint(APIENTRY* PFNGLCREATEPROGRAMPROC) (void);
typedef void (APIENTRY* PFNGLATTACHSHADERPROC) (GLuint program, GLuint shader);
typedef void (APIENTRY* PFNGLLINKPROGRAMPROC) (GLuint program);
typedef void (APIENTRY* PFNGLGETPROGRAMIVPROC) (GLuint program, GLenum pname, GLint* params);
typedef void (APIENTRY* PFNGLGETPROGRAMINFOLOGPROC) (GLuint program, GLsizei bufSize, GLsizei* length, GLchar* infoLog);
typedef void (APIENTRY* PFNGLUSEPROGRAMPROC) (GLuint program);
typedef void (APIENTRY* PFNGLDETACHSHADERPROC) (GLuint program, GLuint shader);
typedef void (APIENTRY* PFNGLDELETESHADERPROC) (GLuint shader);
typedef void (APIENTRY* PFNGLDELETEPROGRAMPROC) (GLuint program);
typedef void (APIENTRY* PFNGLDELETEBUFFERSPROC) (GLsizei n, const GLuint* buffers);
typedef void (APIENTRY* PFNGLDELETEVERTEXARRAYSPROC) (GLsizei n, const GLuint* arrays);
typedef GLint(APIENTRY* PFNGLGETUNIFORMLOCATIONPROC) (GLuint program, const GLchar* name);
typedef void (APIENTRY* PFNGLUNIFORMMATRIX4FVPROC) (GLint location, GLsizei count, GLboolean transpose, const GLfloat* value);
typedef void (APIENTRY* PFNGLUNIFORM1IPROC) (GLint location, GLint v0);

// --- 全局函数指针变量 (Fixed) ---
PFNGLGENBUFFERSPROC             glGenBuffers = nullptr;
PFNGLBINDBUFFERPROC             glBindBuffer = nullptr;
PFNGLBUFFERDATAPROC             glBufferData = nullptr;
PFNGLGENVERTEXARRAYSPROC        glGenVertexArrays = nullptr;
PFNGLBINDVERTEXARRAYPROC        glBindVertexArray = nullptr;
PFNGLENABLEVERTEXATTRIBARRAYPROC glEnableVertexAttribArray = nullptr;
PFNGLVERTEXATTRIBPOINTERPROC    glVertexAttribPointer = nullptr;
PFNGLCREATESHADERPROC           glCreateShader = nullptr;
PFNGLSHADERSOURCEPROC           glShaderSource = nullptr;
PFNGLCOMPILESHADERPROC          glCompileShader = nullptr;
PFNGLGETSHADERIVPROC            glGetShaderiv = nullptr; // <--- 修复了这里
PFNGLGETSHADERINFOLOGPROC       glGetShaderInfoLog = nullptr;
PFNGLCREATEPROGRAMPROC          glCreateProgram = nullptr;
PFNGLATTACHSHADERPROC           glAttachShader = nullptr;
PFNGLLINKPROGRAMPROC            glLinkProgram = nullptr;
PFNGLGETPROGRAMIVPROC           glGetProgramiv = nullptr;
PFNGLGETPROGRAMINFOLOGPROC      glGetProgramInfoLog = nullptr;
PFNGLUSEPROGRAMPROC             glUseProgram = nullptr;
PFNGLDETACHSHADERPROC           glDetachShader = nullptr;
PFNGLDELETESHADERPROC           glDeleteShader = nullptr;
PFNGLDELETEPROGRAMPROC          glDeleteProgram = nullptr;
PFNGLDELETEBUFFERSPROC          glDeleteBuffers = nullptr;
PFNGLDELETEVERTEXARRAYSPROC     glDeleteVertexArrays = nullptr;
PFNGLGETUNIFORMLOCATIONPROC     glGetUniformLocation = nullptr;
PFNGLUNIFORMMATRIX4FVPROC       glUniformMatrix4fv = nullptr;
PFNGLUNIFORM1IPROC              glUniform1i = nullptr;

static void initMiniLoader() {
    glGenBuffers = (PFNGLGENBUFFERSPROC)glfwGetProcAddress("glGenBuffers");
    glBindBuffer = (PFNGLBINDBUFFERPROC)glfwGetProcAddress("glBindBuffer");
    glBufferData = (PFNGLBUFFERDATAPROC)glfwGetProcAddress("glBufferData");
    glGenVertexArrays = (PFNGLGENVERTEXARRAYSPROC)glfwGetProcAddress("glGenVertexArrays");
    glBindVertexArray = (PFNGLBINDVERTEXARRAYPROC)glfwGetProcAddress("glBindVertexArray");
    glEnableVertexAttribArray = (PFNGLENABLEVERTEXATTRIBARRAYPROC)glfwGetProcAddress("glEnableVertexAttribArray");
    glVertexAttribPointer = (PFNGLVERTEXATTRIBPOINTERPROC)glfwGetProcAddress("glVertexAttribPointer");
    glCreateShader = (PFNGLCREATESHADERPROC)glfwGetProcAddress("glCreateShader");
    glShaderSource = (PFNGLSHADERSOURCEPROC)glfwGetProcAddress("glShaderSource");
    glCompileShader = (PFNGLCOMPILESHADERPROC)glfwGetProcAddress("glCompileShader");
    glGetShaderiv = (PFNGLGETSHADERIVPROC)glfwGetProcAddress("glGetShaderiv");
    glGetShaderInfoLog = (PFNGLGETSHADERINFOLOGPROC)glfwGetProcAddress("glGetShaderInfoLog");
    glCreateProgram = (PFNGLCREATEPROGRAMPROC)glfwGetProcAddress("glCreateProgram");
    glAttachShader = (PFNGLATTACHSHADERPROC)glfwGetProcAddress("glAttachShader");
    glLinkProgram = (PFNGLLINKPROGRAMPROC)glfwGetProcAddress("glLinkProgram");
    glGetProgramiv = (PFNGLGETPROGRAMIVPROC)glfwGetProcAddress("glGetProgramiv");
    glGetProgramInfoLog = (PFNGLGETPROGRAMINFOLOGPROC)glfwGetProcAddress("glGetProgramInfoLog");
    glUseProgram = (PFNGLUSEPROGRAMPROC)glfwGetProcAddress("glUseProgram");
    glDetachShader = (PFNGLDETACHSHADERPROC)glfwGetProcAddress("glDetachShader");
    glDeleteShader = (PFNGLDELETESHADERPROC)glfwGetProcAddress("glDeleteShader");
    glDeleteProgram = (PFNGLDELETEPROGRAMPROC)glfwGetProcAddress("glDeleteProgram");
    glDeleteBuffers = (PFNGLDELETEBUFFERSPROC)glfwGetProcAddress("glDeleteBuffers");
    glDeleteVertexArrays = (PFNGLDELETEVERTEXARRAYSPROC)glfwGetProcAddress("glDeleteVertexArrays");
    glGetUniformLocation = (PFNGLGETUNIFORMLOCATIONPROC)glfwGetProcAddress("glGetUniformLocation");
    glUniformMatrix4fv = (PFNGLUNIFORMMATRIX4FVPROC)glfwGetProcAddress("glUniformMatrix4fv");
    glUniform1i = (PFNGLUNIFORM1IPROC)glfwGetProcAddress("glUniform1i");
}

static constexpr float PI = 3.14159265358979323846f;

// Shader 辅助函数
static GLuint compileShader(GLenum type, const char* src) {
    GLuint shader = glCreateShader(type);
    glShaderSource(shader, 1, &src, nullptr);
    glCompileShader(shader);
    GLint ok = 0; glGetShaderiv(shader, GL_COMPILE_STATUS, &ok);
    if (!ok) {
        GLint len = 0; glGetShaderiv(shader, GL_INFO_LOG_LENGTH, &len);
        std::vector<char> log(len);
        glGetShaderInfoLog(shader, len, nullptr, log.data());
        std::cerr << "Shader compile error:\n" << log.data() << std::endl;
    }
    return shader;
}

static GLuint linkProgram(GLuint vs, GLuint fs) {
    GLuint prog = glCreateProgram();
    glAttachShader(prog, vs);
    glAttachShader(prog, fs);
    glLinkProgram(prog);
    GLint ok = 0; glGetProgramiv(prog, GL_LINK_STATUS, &ok);
    if (!ok) {
        GLint len = 0; glGetProgramiv(prog, GL_INFO_LOG_LENGTH, &len);
        std::vector<char> log(len);
        glGetProgramInfoLog(prog, len, nullptr, log.data());
        std::cerr << "Program link error:\n" << log.data() << std::endl;
    }
    glDetachShader(prog, vs);
    glDetachShader(prog, fs);
    glDeleteShader(vs);
    glDeleteShader(fs);
    return prog;
}

// Vertex Shader
static const char* kVertexShader = R"(#version 330 core
layout(location=0) in vec3 aPos;
layout(location=1) in vec3 aNormal;
uniform mat4 uModel;
uniform mat4 uView;
uniform mat4 uProj;
uniform mat4 uParams0; 
uniform mat4 uParams1; 
uniform int  uShadingMode;
out vec3 vWorldPos;
out vec3 vNormal;
out vec3 vGouraudColor;
void main() {
    vec4 worldPos = uModel * vec4(aPos, 1.0);
    vWorldPos = worldPos.xyz;
    vNormal = mat3(transpose(inverse(uModel))) * aNormal;
    gl_Position = uProj * uView * worldPos;
    if (uShadingMode == 1) { 
        vec3 N = normalize(vNormal);
        float ambientIntensity  = uParams0[0][0];
        float diffuseIntensity  = uParams0[0][1];
        float specularIntensity = uParams0[0][2];
        float shininess         = uParams0[0][3];
        vec3 lightPos  = vec3(uParams1[0][0], uParams1[0][1], uParams1[0][2]);
        vec3 cameraPos = vec3(uParams1[1][0], uParams1[1][1], uParams1[1][2]);
        vec3 baseColor = vec3(uParams1[2][0], uParams1[2][1], uParams1[2][2]);
        vec3 L = normalize(lightPos - vWorldPos);
        vec3 V = normalize(cameraPos - vWorldPos);
        vec3 ambient = ambientIntensity * vec3(1.0) * baseColor;
        float diff = max(dot(N, L), 0.0);
        vec3 diffuse = diffuseIntensity * diff * vec3(1.0) * baseColor;
        vec3 R = reflect(-L, N);
        float spec = pow(max(dot(V, R), 0.0), shininess);
        vec3 specular = specularIntensity * spec * vec3(1.0);
        vGouraudColor = ambient + diffuse + specular;
    } else { vGouraudColor = vec3(0.0); }
}
)";

// Fragment Shader
static const char* kFragmentShader = R"(#version 330 core
in vec3 vWorldPos;
in vec3 vNormal;
in vec3 vGouraudColor;
out vec4 FragColor;
uniform mat4 uParams0;
uniform mat4 uParams1;
uniform int  uShadingMode;
void main() {
    vec3 finalColor;
    if (uShadingMode == 1) {
        finalColor = vGouraudColor;
    } else {
        vec3 N = normalize(vNormal);
        float ambientIntensity  = uParams0[0][0];
        float diffuseIntensity  = uParams0[0][1];
        float specularIntensity = uParams0[0][2];
        float shininess         = uParams0[0][3];
        vec3 lightPos  = vec3(uParams1[0][0], uParams1[0][1], uParams1[0][2]);
        vec3 cameraPos = vec3(uParams1[1][0], uParams1[1][1], uParams1[1][2]);
        vec3 baseColor = vec3(uParams1[2][0], uParams1[2][1], uParams1[2][2]);
        vec3 L = normalize(lightPos - vWorldPos);
        vec3 V = normalize(cameraPos - vWorldPos);
        vec3 ambient = ambientIntensity * vec3(1.0) * baseColor;
        float diff = max(dot(N, L), 0.0);
        vec3 diffuse = diffuseIntensity * diff * vec3(1.0) * baseColor;
        vec3 R = reflect(-L, N);
        float spec = pow(max(dot(V, R), 0.0), shininess);
        vec3 specular = specularIntensity * spec * vec3(1.0);
        finalColor = ambient + diffuse + specular;
    }
    FragColor = vec4(clamp(finalColor, 0.0, 1.0), 1.0);
}
)";

struct Mesh {
    std::vector<float> vertices;
    std::vector<unsigned int> indices;
    std::vector<float> nonIndexedVertices;
};

static Mesh makeSphere(unsigned stacks, unsigned slices, float radius = 0.6f) {
    Mesh m;
    std::vector<float> rawVerts;
    rawVerts.reserve((stacks + 1) * (slices + 1) * 6);
    for (unsigned i = 0; i <= stacks; ++i) {
        float v = float(i) / stacks; float phi = v * PI;
        for (unsigned j = 0; j <= slices; ++j) {
            float u = float(j) / slices; float theta = u * 2.0f * PI;
            float x = radius * sinf(phi) * cosf(theta);
            float y = radius * cosf(phi);
            float z = radius * sinf(phi) * sinf(theta);
            float nx = x / radius; float ny = y / radius; float nz = z / radius;
            rawVerts.push_back(x); rawVerts.push_back(y); rawVerts.push_back(z);
            rawVerts.push_back(nx); rawVerts.push_back(ny); rawVerts.push_back(nz);
        }
    }
    m.vertices = rawVerts;
    for (unsigned i = 0; i < stacks; ++i) {
        for (unsigned j = 0; j < slices; ++j) {
            unsigned a = i * (slices + 1) + j; unsigned b = a + slices + 1;
            m.indices.push_back(a); m.indices.push_back(b); m.indices.push_back(a + 1);
            m.indices.push_back(b); m.indices.push_back(b + 1); m.indices.push_back(a + 1);
        }
    }
    for (unsigned int idx : m.indices) {
        for (int k = 0; k < 6; ++k) m.nonIndexedVertices.push_back(rawVerts[idx * 6 + k]);
    }
    return m;
}

struct GLMesh {
    GLuint vao = 0, vbo = 0, ebo = 0;
    GLsizei indexCount = 0;
    GLsizei vertexCount = 0;
};

static GLMesh uploadMesh(const Mesh& m, bool useIndex) {
    GLMesh gm;
    glGenVertexArrays(1, &gm.vao);
    glGenBuffers(1, &gm.vbo);
    glBindVertexArray(gm.vao);
    glBindBuffer(GL_ARRAY_BUFFER, gm.vbo);
    if (useIndex) {
        glBufferData(GL_ARRAY_BUFFER, m.vertices.size() * sizeof(float), m.vertices.data(), GL_STATIC_DRAW);
        glGenBuffers(1, &gm.ebo);
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, gm.ebo);
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, m.indices.size() * sizeof(unsigned int), m.indices.data(), GL_STATIC_DRAW);
        gm.indexCount = (GLsizei)m.indices.size();
    }
    else {
        glBufferData(GL_ARRAY_BUFFER, m.nonIndexedVertices.size() * sizeof(float), m.nonIndexedVertices.data(), GL_STATIC_DRAW);
        gm.vertexCount = (GLsizei)(m.nonIndexedVertices.size() / 6);
    }
    glEnableVertexAttribArray(0); glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 6 * sizeof(float), (void*)0);
    glEnableVertexAttribArray(1); glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 6 * sizeof(float), (void*)(3 * sizeof(float)));
    glBindVertexArray(0);
    return gm;
}

int main() {
    if (!glfwInit()) return -1;
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_COMPAT_PROFILE);

    GLFWwindow* win = glfwCreateWindow(1200, 800, "HW3: Efficiency Analysis", nullptr, nullptr);
    if (!win) { glfwTerminate(); return -1; }
    glfwMakeContextCurrent(win);
    glfwSwapInterval(1); // V-Sync

    initMiniLoader();

    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGui::StyleColorsDark();
    ImGui_ImplGlfw_InitForOpenGL(win, true);
    ImGui_ImplOpenGL3_Init("#version 330");

    GLuint vs = compileShader(GL_VERTEX_SHADER, kVertexShader);
    GLuint fs = compileShader(GL_FRAGMENT_SHADER, kFragmentShader);
    GLuint prog = linkProgram(vs, fs);

    Mesh sphere = makeSphere(64,64, 0.6f);
    GLMesh meshIndexed = uploadMesh(sphere, true);
    GLMesh meshNoIndex = uploadMesh(sphere, false);

    glEnable(GL_DEPTH_TEST);
    glClearColor(0.1f, 0.1f, 0.12f, 1.0f);

    int shadingMode = 0; 
    int drawMode = 0;    
    bool autoRotate = true; 
    float rotationSpeed = 30.0f;
    float rotY = 0.0f;
    float ambientI = 0.1f, diffuseI = 0.8f, specularI = 0.6f, shininess = 32.0f;
    float lightPos[3] = { 2.0f, 2.0f, 2.0f };
    float baseColor[3] = { 1.0f, 0.5f, 0.0f };

    // --- 性能统计变量 ---
    double renderTimeAccum = 0.0;
    int renderFrameCount = 0;
    float displayRenderTime = 0.0f;

    while (!glfwWindowShouldClose(win)) {
        glfwPollEvents();
        ImGui_ImplOpenGL3_NewFrame();
        ImGui_ImplGlfw_NewFrame();
        ImGui::NewFrame();

        // --- 控制面板 ---
        ImGui::Begin("Control Panel");
        // 显示核心渲染时间（不包含 SwapBuffer 等待）
        ImGui::TextColored(ImVec4(0,1,0,1), "Core Render Time: %.3f ms", displayRenderTime);
        ImGui::Text("FPS: %.1f", ImGui::GetIO().Framerate);
        
        if (ImGui::CollapsingHeader("Settings", ImGuiTreeNodeFlags_DefaultOpen)) {
            ImGui::SeparatorText("Rotation");
            ImGui::Checkbox("Auto Rotate", &autoRotate);
            ImGui::SliderFloat("Speed", &rotationSpeed, 0.0f, 200.0f);
            ImGui::SliderFloat("Angle Y", &rotY, 0.0f, 360.0f);

            ImGui::SeparatorText("Render Mode");
            ImGui::RadioButton("Phong", &shadingMode, 0);
            ImGui::RadioButton("Gouraud", &shadingMode, 1);

            ImGui::SeparatorText("Draw Method");
            ImGui::RadioButton("VBO Indexed", &drawMode, 0);
            ImGui::RadioButton("VBO Array", &drawMode, 1);
            ImGui::RadioButton("Immediate (glBegin)", &drawMode, 2);
            if (drawMode == 2) ImGui::TextColored(ImVec4(1, 0, 0, 1), "Warning: High CPU Overhead");

            ImGui::SeparatorText("Light & Material");
            ImGui::ColorEdit3("Color", baseColor);
            ImGui::SliderFloat("Shininess", &shininess, 1.0f, 128.0f);
            ImGui::SliderFloat("Ambient", &ambientI, 0.0f, 1.0f);
            ImGui::SliderFloat("Diffuse", &diffuseI, 0.0f, 1.0f);
            ImGui::SliderFloat("Specular", &specularI, 0.0f, 1.0f);
        }
        ImGui::End();

        // --- 更新 ---
        int width, height;
        glfwGetFramebufferSize(win, &width, &height);
        glViewport(0, 0, width, height);
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

        if (autoRotate) {
            rotY += ImGui::GetIO().DeltaTime * rotationSpeed;
            if (rotY > 360.0f) rotY -= 360.0f;
            if (rotY < 0.0f) rotY += 360.0f;
        }

        // 矩阵准备
        float aspect = (float)width / (float)(height > 0 ? height : 1);
        float f = 1.0f / tanf(45.0f * PI / 360.0f);
        float zNear = 0.1f, zFar = 100.0f;
        std::vector<float> P = { f/aspect,0,0,0, 0,f,0,0, 0,0,(zFar+zNear)/(zNear-zFar),-1, 0,0,(2*zFar*zNear)/(zNear-zFar),0 };
        std::vector<float> V = { 1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,-2.5f,1 };
        float c = cosf(rotY * PI / 180), s = sinf(rotY * PI / 180);
        std::vector<float> M = { c,0,-s,0, 0,1,0,0, s,0,c,0, 0,0,0,1 };
        float p0[] = { ambientI, diffuseI, specularI, shininess, 0,0,0,0, 0,0,0,0, 0,0,0,0 };
        float p1[] = { lightPos[0], lightPos[1], lightPos[2], 1.0f,  0,0,2.5f,1,  baseColor[0], baseColor[1], baseColor[2], 1,  0,0,0,0 };

        // ============================================
        // 核心性能统计开始 (Core Performance Measure)
        // ============================================
        double tStart = glfwGetTime(); // 记录开始时间

        if (drawMode != 2) {
            // --- VBO 模式 (GPU Bound) ---
            glUseProgram(prog);
            glUniformMatrix4fv(glGetUniformLocation(prog, "uProj"), 1, GL_FALSE, P.data());
            glUniformMatrix4fv(glGetUniformLocation(prog, "uView"), 1, GL_FALSE, V.data());
            glUniformMatrix4fv(glGetUniformLocation(prog, "uModel"), 1, GL_FALSE, M.data());
            glUniformMatrix4fv(glGetUniformLocation(prog, "uParams0"), 1, GL_FALSE, p0);
            glUniformMatrix4fv(glGetUniformLocation(prog, "uParams1"), 1, GL_FALSE, p1);
            glUniform1i(glGetUniformLocation(prog, "uShadingMode"), shadingMode);

            if (drawMode == 0) {
                glBindVertexArray(meshIndexed.vao);
                glDrawElements(GL_TRIANGLES, meshIndexed.indexCount, GL_UNSIGNED_INT, 0);
            }
            else {
                glBindVertexArray(meshNoIndex.vao);
                glDrawArrays(GL_TRIANGLES, 0, meshNoIndex.vertexCount);
            }
            glBindVertexArray(0);
        }
        else {
            // --- Immediate Mode (CPU Bound) ---
            glUseProgram(0); 
            glMatrixMode(GL_PROJECTION); glLoadMatrixf(P.data());
            glMatrixMode(GL_MODELVIEW); glLoadIdentity();
            glLoadMatrixf(V.data()); glMultMatrixf(M.data());

            glEnable(GL_LIGHTING); glEnable(GL_LIGHT0);
            GLfloat lp[] = { lightPos[0], lightPos[1], lightPos[2], 1.0f };
            glLightfv(GL_LIGHT0, GL_POSITION, lp);
            glEnable(GL_COLOR_MATERIAL);
            glColor3f(baseColor[0], baseColor[1], baseColor[2]);

            glBegin(GL_TRIANGLES);
            const auto& verts = sphere.nonIndexedVertices;
            for (size_t i = 0; i < verts.size(); i += 6) {
                glNormal3f(verts[i + 3], verts[i + 4], verts[i + 5]);
                glVertex3f(verts[i], verts[i + 1], verts[i + 2]);
            }
            glEnd();
            glDisable(GL_LIGHTING);
        }

        // ============================================
        // 核心性能统计结束
        // ============================================
        double tEnd = glfwGetTime(); // 记录结束时间
        
        // 累积时间
        renderTimeAccum += (tEnd - tStart) * 1000.0;
        renderFrameCount++;

        // 每 60 帧更新一次显示数据，避免数字跳动过快
        if (renderFrameCount >= 60) {
            displayRenderTime = (float)(renderTimeAccum / renderFrameCount);
            renderTimeAccum = 0.0;
            renderFrameCount = 0;
        }

        // --- 渲染 ImGui ---
        ImGui::Render();
        ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());
        glfwSwapBuffers(win);
    }

    ImGui_ImplOpenGL3_Shutdown();
    ImGui_ImplGlfw_Shutdown();
    ImGui::DestroyContext();

    glfwDestroyWindow(win);
    glfwTerminate();
    return 0;
}