//=======================================运行前先重命名为main.cpp========================================
#include <GLFW/glfw3.h>
#include <cmath>
#include <iostream>

// 字母M的顶点（8个三角形）
const int letterM[] = {
    0, 0, 0, 0, 7, 0, 1, 0, 0,
    1, 0, 0, 0, 7, 0, 1, 5, 0,
    0, 7, 0, 1, 5, 0, 3, 4, 0,
    1, 5, 0, 3, 4, 0, 3, 3, 0,
    3, 4, 0, 3, 3, 0, 5, 5, 0,
    3, 4, 0, 5, 5, 0, 6, 7, 0,
    5, 0, 0, 5, 5, 0, 6, 7, 0,
    5, 0, 0, 6, 7, 0, 6, 0, 0
};

// 字母F的顶点（6个三角形）
const int letterF[] = {
    8, 0, 0, 8, 6, 0, 9, 0, 0,
    9, 0, 0, 8, 6, 0, 9, 6, 0,
    8, 6, 0, 13, 6, 0, 8, 7, 0,
    8, 7, 0, 13, 6, 0, 13, 7, 0,
    9, 3, 0, 12, 3, 0, 9, 4, 0,
    9, 4, 0, 12, 3, 0, 12, 4, 0
};

// 字母Q的顶点（11个三角形）
const int letterQ[] = {
    20, 0, 0, 19, 1, 0, 21, 1, 0,
    16, 1, 0, 21, 1, 0, 20, 2, 0,
    15, 2, 0, 16, 1, 0, 20, 2, 0,
    15, 2, 0, 17, 2, 0, 15, 4, 0,
    20, 2, 0, 18, 2, 0, 20, 4, 0,
    16, 3, 0, 15, 4, 0, 16, 5, 0,
    19, 3, 0, 20, 4, 0, 19, 5, 0,
    15, 4, 0, 15, 6, 0, 17, 6, 0,
    20, 4, 0, 20, 6, 0, 18, 6, 0,
    15, 6, 0, 20, 6, 0, 16, 7, 0,
    16, 7, 0, 19, 7, 0, 20, 6, 0
};

void drawLetter(const int* vertices, int triangleCount) {
    glBegin(GL_TRIANGLES);
    for (int i = 0; i < triangleCount * 9; i += 3) {
        glVertex3i(vertices[i], vertices[i + 1], vertices[i + 2]);
    }
    glEnd();
}

void setViewMatrix(float eyeX, float eyeY, float eyeZ,
    float centerX, float centerY, float centerZ,
    float upX, float upY, float upZ) {
    // 计算前向向量
    float forward[3] = {
        centerX - eyeX,
        centerY - eyeY,
        centerZ - eyeZ
    };

    // 归一化前向向量
    float length = sqrt(forward[0] * forward[0] + forward[1] * forward[1] + forward[2] * forward[2]);
    if (length > 0) {
        forward[0] /= length;
        forward[1] /= length;
        forward[2] /= length;
    }

    // 归一化上向量
    float up[3] = { upX, upY, upZ };
    length = sqrt(up[0] * up[0] + up[1] * up[1] + up[2] * up[2]);
    if (length > 0) {
        up[0] /= length;
        up[1] /= length;
        up[2] /= length;
    }

    // 计算右向量（侧向量）
    float right[3] = {
        forward[1] * up[2] - forward[2] * up[1],
        forward[2] * up[0] - forward[0] * up[2],
        forward[0] * up[1] - forward[1] * up[0]
    };

    // 归一化右向量
    length = sqrt(right[0] * right[0] + right[1] * right[1] + right[2] * right[2]);
    if (length > 0) {
        right[0] /= length;
        right[1] /= length;
        right[2] /= length;
    }

    // 重新计算上向量（确保与forward和right垂直）
    up[0] = right[1] * forward[2] - right[2] * forward[1];
    up[1] = right[2] * forward[0] - right[0] * forward[2];
    up[2] = right[0] * forward[1] - right[1] * forward[0];

    // 构建视图矩阵
    float viewMatrix[16] = {
        right[0], up[0], -forward[0], 0.0f,
        right[1], up[1], -forward[1], 0.0f,
        right[2], up[2], -forward[2], 0.0f,
        0.0f, 0.0f, 0.0f, 1.0f
    };

    glMultMatrixf(viewMatrix);
    glTranslatef(-eyeX, -eyeY, -eyeZ);
}

void setProjection(int mode, float d) {
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();

    float aspect = 640.0f / 480.0f;
    float near = 1.0f;
    float far = 100.0f;

    switch (mode) {
    case 0: // 正交投影 + 视角1
        glOrtho(-20.0f, 30.0f, -15.0f, 20.0f, near, far);
        break;
    case 1: // 透视投影 + 视角1
    {
        float fovy = 75.0f; 
        float top = tan(fovy * 3.14159f / 360.0f) * near;
        float right = top * aspect;
        glFrustum(-right * 1.5f, right * 1.5f, -top * 1.5f, top * 1.5f, near, far);
        break;
    }
    case 2: // 正交投影 + 视角2
        glOrtho(-20.0f, 30.0f, -15.0f, 20.0f, near, far);
        break;
    case 3: // 透视投影 + 视角2
    {
        float fovy = 75.0f; 
        float top = tan(fovy * 3.14159f / 360.0f) * near;
        float right = top * aspect;
        glFrustum(-right * 1.5f, right * 1.5f, -top * 1.5f, top * 1.5f, near, far);
        break;
    }
    }

    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();

    // 设置视角
    switch (mode) {
    case 0: // 正交+视角1
        setViewMatrix(0.0f, 0.0f, d, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f);
        break;
    case 1: // 透视+视角1
        setViewMatrix(0.0f, 0.0f, d * 0.8f, 0.0f, 3.5f, 0.0f, 0.0f, 1.0f, 0.0f);
        break;
    case 2: // 正交+视角2
        setViewMatrix(0.0f, 0.5f * d, d, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f);
        break;
    case 3: // 透视+视角2
        setViewMatrix(0.0f, 0.5f * d, d * 0.8f, 0.0f, 3.5f, 0.0f, 0.0f, 1.0f, 0.0f);
        break;
    }
}

int main(void) {
    if (!glfwInit())
        return -1;

    GLFWwindow* window = glfwCreateWindow(640, 480, "投影与视角比较", NULL, NULL);
    if (!window) {
        glfwTerminate();
        return -1;
    }
    glfwMakeContextCurrent(window);

    int mode = 0;
    float d = 30.0f; // 增加观察距离

    std::cout << "=== 投影与视角比较 ===" << std::endl;
    std::cout << "按键说明:" << std::endl;
    std::cout << "1: 正交投影 + 视角1(平视)" << std::endl;
    std::cout << "2: 透视投影 + 视角1(平视)" << std::endl;
    std::cout << "3: 正交投影 + 视角2(俯视)" << std::endl;
    std::cout << "4: 透视投影 + 视角2(俯视)" << std::endl;

    while (!glfwWindowShouldClose(window)) {
        glfwPollEvents();

        if (glfwGetKey(window, GLFW_KEY_1) == GLFW_PRESS) mode = 0;
        if (glfwGetKey(window, GLFW_KEY_2) == GLFW_PRESS) mode = 1;
        if (glfwGetKey(window, GLFW_KEY_3) == GLFW_PRESS) mode = 2;
        if (glfwGetKey(window, GLFW_KEY_4) == GLFW_PRESS) mode = 3;

        int width, height;
        glfwGetFramebufferSize(window, &width, &height);
        glViewport(0, 0, width, height);
        glClear(GL_COLOR_BUFFER_BIT);

        setProjection(mode, d);

        // 绘制字母
        glColor3f(1.0f, 0.0f, 0.0f);
        drawLetter(letterM, 8);

        glColor3f(0.0f, 1.0f, 0.0f);
        drawLetter(letterF, 6);

        glColor3f(0.0f, 0.0f, 1.0f);
        drawLetter(letterQ, 11);

        glfwSwapBuffers(window);
    }

    glfwTerminate();
    return 0;
}