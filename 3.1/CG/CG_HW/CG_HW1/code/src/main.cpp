#include <GLFW/glfw3.h>
#include <cmath>
#include <iostream>
#include <vector>

// 3D顶点结构
struct Vertex {
    float x, y, z;
    Vertex(float x, float y, float z) : x(x), y(y), z(z) {}
};

// 三角形结构
struct Triangle {
    Vertex v1, v2, v3;
    Triangle(Vertex v1, Vertex v2, Vertex v3) : v1(v1), v2(v2), v3(v3) {}
};

// 立体字母M的三角形集合
std::vector<Triangle> letterM3D;

// 厚度
const float THICKNESS = 2.0;

// 旋转角度
float angleX = 0.0f;
float angleY = 0.0f;
float angleZ = 0.0f;

// 旋转速度
float rotationSpeed = 1.0f;

// 是否自动旋转
bool autoRotate = true;

// 当前旋转轴 (0:x, 1:y, 2:z, 3:组合)
int rotationAxis = 0;

// 初始化立体字母M
void init3DLetterM() {
    // 2D字母M的顶点（原始平面）
    std::vector<Vertex> frontVertices = {
        Vertex(0, 0, 0), Vertex(0, 7, 0), Vertex(1, 0, 0),
        Vertex(1, 0, 0), Vertex(0, 7, 0), Vertex(1, 5, 0),
        Vertex(0, 7, 0), Vertex(1, 5, 0), Vertex(3, 4, 0),
        Vertex(1, 5, 0), Vertex(3, 4, 0), Vertex(3, 3, 0),
        Vertex(3, 4, 0), Vertex(3, 3, 0), Vertex(5, 5, 0),
        Vertex(3, 4, 0), Vertex(5, 5, 0), Vertex(6, 7, 0),
        Vertex(5, 0, 0), Vertex(5, 5, 0), Vertex(6, 7, 0),
        Vertex(5, 0, 0), Vertex(6, 7, 0), Vertex(6, 0, 0)
    };

    // 创建后表面（z坐标为负厚度）
    std::vector<Vertex> backVertices;
    for (const auto& v : frontVertices) {
        backVertices.push_back(Vertex(v.x, v.y, -THICKNESS));
    }

    // 添加前表面三角形
    for (int i = 0; i < frontVertices.size(); i += 3) {
        letterM3D.push_back(Triangle(
            frontVertices[i],
            frontVertices[i + 1],
            frontVertices[i + 2]
        ));
    }

    // 添加后表面三角形（顶点顺序反转以实现正确的面法线）
    for (int i = 0; i < backVertices.size(); i += 3) {
        letterM3D.push_back(Triangle(
            backVertices[i + 2],  // 反转顶点顺序
            backVertices[i + 1],
            backVertices[i]
        ));
    }

    // 添加侧面（连接前表面和后表面的四边形，每个四边形由2个三角形组成）
    for (int i = 0; i < frontVertices.size(); i += 3) {
        // 对于每个三角形的每条边
        for (int j = 0; j < 3; j++) {
            int current = i + j;
            int next = i + ((j + 1) % 3);

            Vertex v1_front = frontVertices[current];
            Vertex v2_front = frontVertices[next];
            Vertex v1_back = backVertices[current];
            Vertex v2_back = backVertices[next];

            // 第一个三角形
            letterM3D.push_back(Triangle(v1_front, v2_front, v1_back));
            // 第二个三角形
            letterM3D.push_back(Triangle(v2_front, v2_back, v1_back));
        }
    }
}

// 绘制立体字母M
void draw3DLetterM() {
    glBegin(GL_TRIANGLES);

    for (const auto& triangle : letterM3D) {
        // 前表面 - 红色
        if (triangle.v1.z == 0 && triangle.v2.z == 0 && triangle.v3.z == 0) {
            glColor3f(1.0f, 0.0f, 0.0f); // 红色
        }
        // 后表面 - 蓝色
        else if (triangle.v1.z == -THICKNESS && triangle.v2.z == -THICKNESS && triangle.v3.z == -THICKNESS) {
            glColor3f(0.0f, 0.0f, 1.0f); // 蓝色
        }
        // 侧面 - 绿色
        else {
            glColor3f(0.0f, 1.0f, 0.0f); // 绿色
        }

        glVertex3f(triangle.v1.x, triangle.v1.y, triangle.v1.z);
        glVertex3f(triangle.v2.x, triangle.v2.y, triangle.v2.z);
        glVertex3f(triangle.v3.x, triangle.v3.y, triangle.v3.z);
    }

    glEnd();
}

// 设置视图矩阵
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

    // 计算右向量
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

    // 重新计算上向量
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

// 设置投影
void setProjection() {
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();

    float aspect = 640.0f / 480.0f;
    float near = 1.0f;
    float far = 100.0f;

    // 使用透视投影
    float fovy = 60.0f;
    float top = tan(fovy * 3.14159f / 360.0f) * near;
    float right = top * aspect;
    glFrustum(-right, right, -top, top, near, far);

    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();

    // 设置视角 - 从斜上方观看
    setViewMatrix(10.0f, 8.0f, 15.0f, 3.0f, 3.5f, 0.0f, 0.0f, 1.0f, 0.0f);
}

int main(void) {
    if (!glfwInit())
        return -1;

    GLFWwindow* window = glfwCreateWindow(640, 480, "立体字母M旋转演示", NULL, NULL);
    if (!window) {
        glfwTerminate();
        return -1;
    }
    glfwMakeContextCurrent(window);

    // 初始化立体字母M
    init3DLetterM();

    // 启用深度测试
    glEnable(GL_DEPTH_TEST);

    std::cout << "=== 立体字母M旋转演示 ===" << std::endl;
    std::cout << "按键说明:" << std::endl;
    std::cout << "X: 绕X轴旋转" << std::endl;
    std::cout << "Y: 绕Y轴旋转" << std::endl;
    std::cout << "Z: 绕Z轴旋转" << std::endl;
    std::cout << "A: 绕XYZ组合旋转" << std::endl;
    std::cout << "R: 重置旋转" << std::endl;
    std::cout << "空格: 切换自动/手动旋转" << std::endl;
    std::cout << "+/-: 增加/减少旋转速度" << std::endl;
    std::cout << "颜色说明:" << std::endl;
    std::cout << "红色: 前表面" << std::endl;
    std::cout << "蓝色: 后表面" << std::endl;
    std::cout << "绿色: 侧面" << std::endl;

    while (!glfwWindowShouldClose(window)) {
        glfwPollEvents();

        // 处理键盘输入
        if (glfwGetKey(window, GLFW_KEY_X) == GLFW_PRESS) {
            rotationAxis = 0; // X轴
            autoRotate = true;
        }
        if (glfwGetKey(window, GLFW_KEY_Y) == GLFW_PRESS) {
            rotationAxis = 1; // Y轴
            autoRotate = true;
        }
        if (glfwGetKey(window, GLFW_KEY_Z) == GLFW_PRESS) {
            rotationAxis = 2; // Z轴
            autoRotate = true;
        }
        if (glfwGetKey(window, GLFW_KEY_A) == GLFW_PRESS) {
            rotationAxis = 3; // 组合旋转
            autoRotate = true;
        }
        if (glfwGetKey(window, GLFW_KEY_R) == GLFW_PRESS) {
            angleX = angleY = angleZ = 0.0f; // 重置
        }
        if (glfwGetKey(window, GLFW_KEY_SPACE) == GLFW_PRESS) {
            autoRotate = !autoRotate; // 切换自动/手动
            // 防抖
            while (glfwGetKey(window, GLFW_KEY_SPACE) == GLFW_PRESS) {
                glfwPollEvents();
            }
        }
        if (glfwGetKey(window, GLFW_KEY_EQUAL) == GLFW_PRESS) {
            rotationSpeed += 0.1f; // 加速
        }
        if (glfwGetKey(window, GLFW_KEY_MINUS) == GLFW_PRESS) {
            rotationSpeed = std::max(0.1f, rotationSpeed - 0.1f); // 减速
        }

        // 手动旋转控制
        if (!autoRotate) {
            if (glfwGetKey(window, GLFW_KEY_LEFT) == GLFW_PRESS) {
                angleY -= rotationSpeed;
            }
            if (glfwGetKey(window, GLFW_KEY_RIGHT) == GLFW_PRESS) {
                angleY += rotationSpeed;
            }
            if (glfwGetKey(window, GLFW_KEY_UP) == GLFW_PRESS) {
                angleX -= rotationSpeed;
            }
            if (glfwGetKey(window, GLFW_KEY_DOWN) == GLFW_PRESS) {
                angleX += rotationSpeed;
            }
            if (glfwGetKey(window, GLFW_KEY_Q) == GLFW_PRESS) {
                angleZ -= rotationSpeed;
            }
            if (glfwGetKey(window, GLFW_KEY_E) == GLFW_PRESS) {
                angleZ += rotationSpeed;
            }
        }

        int width, height;
        glfwGetFramebufferSize(window, &width, &height);
        glViewport(0, 0, width, height);
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

        setProjection();

        // 应用旋转
        if (autoRotate) {
            switch (rotationAxis) {
            case 0: // X轴
                angleX += rotationSpeed;
                break;
            case 1: // Y轴
                angleY += rotationSpeed;
                break;
            case 2: // Z轴
                angleZ += rotationSpeed;
                break;
            case 3: // 组合旋转
                angleX += rotationSpeed;
                angleY += rotationSpeed * 0.7f;
                angleZ += rotationSpeed * 0.3f;
                break;
            }
        }

        // 应用旋转变换
        glRotatef(angleX, 1.0f, 0.0f, 0.0f); // 绕X轴旋转
        glRotatef(angleY, 0.0f, 1.0f, 0.0f); // 绕Y轴旋转
        glRotatef(angleZ, 0.0f, 0.0f, 1.0f); // 绕Z轴旋转

        // 将字母居中
        glTranslatef(-3.0f, -3.5f, 0.0f);

        // 绘制立体字母M
        draw3DLetterM();

        glfwSwapBuffers(window);
    }

    glfwTerminate();
    return 0;
}