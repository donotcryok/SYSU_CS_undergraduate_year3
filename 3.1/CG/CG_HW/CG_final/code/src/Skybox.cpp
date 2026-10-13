#include "Skybox.h"
#include <glm/gtc/type_ptr.hpp>

#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <wincodec.h>
#pragma comment(lib, "windowscodecs.lib")
#endif

bool Skybox::init(const std::wstring& texturePath) {
    // 1. Load Texture
    textureID = loadTextureWIC(texturePath);
    if (textureID == 0) return false;

    // 2. Create Cube Mesh (Positions only)
    float skyboxVertices[] = {
        // positions          
        -1.0f,  1.0f, -1.0f,
        -1.0f, -1.0f, -1.0f,
         1.0f, -1.0f, -1.0f,
         1.0f, -1.0f, -1.0f,
         1.0f,  1.0f, -1.0f,
        -1.0f,  1.0f, -1.0f,

        -1.0f, -1.0f,  1.0f,
        -1.0f, -1.0f, -1.0f,
        -1.0f,  1.0f, -1.0f,
        -1.0f,  1.0f, -1.0f,
        -1.0f,  1.0f,  1.0f,
        -1.0f, -1.0f,  1.0f,

         1.0f, -1.0f, -1.0f,
         1.0f, -1.0f,  1.0f,
         1.0f,  1.0f,  1.0f,
         1.0f,  1.0f,  1.0f,
         1.0f,  1.0f, -1.0f,
         1.0f, -1.0f, -1.0f,

        -1.0f, -1.0f,  1.0f,
        -1.0f,  1.0f,  1.0f,
         1.0f,  1.0f,  1.0f,
         1.0f,  1.0f,  1.0f,
         1.0f, -1.0f,  1.0f,
        -1.0f, -1.0f,  1.0f,

        -1.0f,  1.0f, -1.0f,
         1.0f,  1.0f, -1.0f,
         1.0f,  1.0f,  1.0f,
         1.0f,  1.0f,  1.0f,
        -1.0f,  1.0f,  1.0f,
        -1.0f,  1.0f, -1.0f,

        -1.0f, -1.0f, -1.0f,
        -1.0f, -1.0f,  1.0f,
         1.0f, -1.0f, -1.0f,
         1.0f, -1.0f, -1.0f,
        -1.0f, -1.0f,  1.0f,
         1.0f, -1.0f,  1.0f
    };

    glGenVertexArrays(1, &VAO);
    glGenBuffers(1, &VBO);
    glBindVertexArray(VAO);
    glBindBuffer(GL_ARRAY_BUFFER, VBO);
    glBufferData(GL_ARRAY_BUFFER, sizeof(skyboxVertices), &skyboxVertices, GL_STATIC_DRAW);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * sizeof(float), (void*)0);

    // 3. Create Shaders
    const char* vsCode = R"(
#version 330 core
layout (location = 0) in vec3 aPos;

out vec3 localPos;

uniform mat4 view;
uniform mat4 projection;

void main()
{
    localPos = aPos;
    // Remove translation from view matrix
    mat4 viewNoTrans = mat4(mat3(view)); 
    vec4 clipPos = projection * viewNoTrans * vec4(localPos, 1.0);
    
    // Optimization: Set z to w so that z/w = 1.0 (farthest depth)
    gl_Position = clipPos.xyww; 
}
)";

    const char* fsCode = R"(
#version 330 core
out vec4 FragColor;

in vec3 localPos;

uniform sampler2D skybox;

const vec2 invAtan = vec2(0.1591, 0.3183); // 1/(2*PI), 1/PI

void main()
{
    vec3 v = normalize(vec3(localPos.x, localPos.z, -localPos.y));
    // Equirectangular mapping
    vec2 uv = vec2(atan(v.z, v.x), asin(v.y));
    uv *= invAtan;
    uv += 0.5;
    
    FragColor = texture(skybox, uv);
}
)";

    programID = createShader(vsCode, fsCode);
    if (programID == 0) return false;

    glUseProgram(programID);
    glUniform1i(glGetUniformLocation(programID, "skybox"), 0);
    glUseProgram(0);

    return true;
}

void Skybox::render(const glm::mat4& view, const glm::mat4& proj) {
    // Change depth function so depth test passes when values are equal to depth buffer's content
    glDepthFunc(GL_LEQUAL);
    
    glUseProgram(programID);
    glUniformMatrix4fv(glGetUniformLocation(programID, "view"), 1, GL_FALSE, glm::value_ptr(view));
    glUniformMatrix4fv(glGetUniformLocation(programID, "projection"), 1, GL_FALSE, glm::value_ptr(proj));

    glBindVertexArray(VAO);
    glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_2D, textureID);
    glDrawArrays(GL_TRIANGLES, 0, 36);
    glBindVertexArray(0);

    // Set depth function back to default
    glDepthFunc(GL_LESS);
}

GLuint Skybox::createShader(const char* vsCode, const char* fsCode) {
    auto compile = [](GLenum type, const char* src) {
        GLuint s = glCreateShader(type);
        glShaderSource(s, 1, &src, nullptr);
        glCompileShader(s);
        GLint ok; glGetShaderiv(s, GL_COMPILE_STATUS, &ok);
        if (!ok) {
            char log[512]; glGetShaderInfoLog(s, 512, nullptr, log);
            std::cerr << "Shader Error: " << log << std::endl;
        }
        return s;
    };
    GLuint v = compile(GL_VERTEX_SHADER, vsCode);
    GLuint f = compile(GL_FRAGMENT_SHADER, fsCode);
    GLuint p = glCreateProgram();
    glAttachShader(p, v);
    glAttachShader(p, f);
    glLinkProgram(p);
    GLint ok; glGetProgramiv(p, GL_LINK_STATUS, &ok);
    if (!ok) {
        char log[512]; glGetProgramInfoLog(p, 512, nullptr, log);
        std::cerr << "Program Error: " << log << std::endl;
    }
    glDeleteShader(v);
    glDeleteShader(f);
    return p;
}

GLuint Skybox::loadTextureWIC(const std::wstring& filename) {
#ifdef _WIN32
    HRESULT hr = CoInitializeEx(nullptr, COINIT_MULTITHREADED);
    bool didCoInit = SUCCEEDED(hr);
    
    IWICImagingFactory* factory = nullptr;
    IWICBitmapDecoder* decoder = nullptr;
    IWICBitmapFrameDecode* frame = nullptr;
    IWICFormatConverter* converter = nullptr;

    auto cleanup = [&]() {
        if (converter) converter->Release();
        if (frame) frame->Release();
        if (decoder) decoder->Release();
        if (factory) factory->Release();
        if (didCoInit) CoUninitialize();
    };

    hr = CoCreateInstance(CLSID_WICImagingFactory, nullptr, CLSCTX_INPROC_SERVER, IID_PPV_ARGS(&factory));
    if (FAILED(hr)) { cleanup(); return 0; }

    hr = factory->CreateDecoderFromFilename(filename.c_str(), nullptr, GENERIC_READ, WICDecodeMetadataCacheOnLoad, &decoder);
    if (FAILED(hr)) { std::wcerr << L"Failed to load image: " << filename << std::endl; cleanup(); return 0; }

    hr = decoder->GetFrame(0, &frame);
    if (FAILED(hr)) { cleanup(); return 0; }

    hr = factory->CreateFormatConverter(&converter);
    if (FAILED(hr)) { cleanup(); return 0; }

    hr = converter->Initialize(frame, GUID_WICPixelFormat32bppRGBA, WICBitmapDitherTypeNone, nullptr, 0.0, WICBitmapPaletteTypeCustom);
    if (FAILED(hr)) { cleanup(); return 0; }

    UINT w, h;
    converter->GetSize(&w, &h);
    std::vector<unsigned char> buffer(w * h * 4);
    hr = converter->CopyPixels(nullptr, w * 4, (UINT)buffer.size(), buffer.data());
    if (FAILED(hr)) { cleanup(); return 0; }

    // Flip Y
    {
        UINT stride = w * 4;
        std::vector<unsigned char> row(stride);
        for (UINT y = 0; y < h / 2; ++y) {
            unsigned char* top = buffer.data() + y * stride;
            unsigned char* bot = buffer.data() + (h - 1 - y) * stride;
            memcpy(row.data(), top, stride);
            memcpy(top, bot, stride);
            memcpy(bot, row.data(), stride);
        }
    }

    GLuint tex;
    glGenTextures(1, &tex);
    glBindTexture(GL_TEXTURE_2D, tex);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, buffer.data());
    glGenerateMipmap(GL_TEXTURE_2D);
    
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);

    cleanup();
    return tex;
#else
    std::cerr << "WIC not supported on this platform." << std::endl;
    return 0;
#endif
}
