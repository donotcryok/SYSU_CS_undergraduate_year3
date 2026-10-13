#pragma once
#include <string>
#include <glm/glm.hpp>
#include <glad/glad.h>
#include "Model.h"

class TextLabel {
public:
    TextLabel() = default;
    void setText(const std::string& text);
    void setColor(const glm::vec3& c) { color = c; }
    void setTransform(const glm::mat4& m) { modelMatrix = m; }
    void draw(const glm::mat4& view, const glm::mat4& proj);

private:
    void rebuildMesh();
    // 简易 5x7 栅格字形
    static const unsigned char* glyph(char c);

    std::string text = "WIN";
    glm::vec3 color{1.0f, 1.0f, 1.0f};
    glm::mat4 modelMatrix{1.0f};
    Model model;
    GLuint program = 0;
};
