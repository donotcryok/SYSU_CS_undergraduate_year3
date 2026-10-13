#pragma once
#include <glad/glad.h>
#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <vector>
#include <string>
#include <iostream>

class Skybox {
public:
    bool init(const std::wstring& texturePath);
    void render(const glm::mat4& view, const glm::mat4& proj);

private:
    GLuint VAO = 0, VBO = 0;
    GLuint textureID = 0;
    GLuint programID = 0;

    GLuint createShader(const char* vsCode, const char* fsCode);
    GLuint loadTextureWIC(const std::wstring& filename);
};
