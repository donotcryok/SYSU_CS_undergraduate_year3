cmake_minimum_required(VERSION 3.20)
project(ComputerGraphics LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 可根据需要切换构建类型
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

include(FetchContent)

# 1) OpenGL
find_package(OpenGL REQUIRED)

# 2) GLFW: 优先用已安装包，找不到再拉源码
set(GLFW_TARGET "")
find_package(glfw3 CONFIG QUIET)
if(TARGET glfw3::glfw)
  set(GLFW_TARGET glfw3::glfw)
else()
  # 未找到包，使用源码构建
  set(GLFW_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
  set(GLFW_BUILD_TESTS OFF CACHE BOOL "" FORCE)
  set(GLFW_BUILD_DOCS OFF CACHE BOOL "" FORCE)
  FetchContent_Declare(
    glfw
    GIT_REPOSITORY https://github.com/glfw/glfw.git
    GIT_TAG 3.4
  )
  FetchContent_MakeAvailable(glfw)
  # 源码构建的目标名通常为 glfw
  if(TARGET glfw)
    set(GLFW_TARGET glfw)
  endif()
endif()

# 3) GLM: 优先用已安装包，找不到再拉源码
find_package(glm CONFIG QUIET)
if(NOT TARGET glm::glm)
  FetchContent_Declare(
    glm
    GIT_REPOSITORY https://github.com/g-truc/glm.git
    GIT_TAG 1.0.1
  )
  FetchContent_MakeAvailable(glm)
endif()

# 启用 Dear ImGui（GLFW + OpenGL3 后端）
option(ENABLE_IMGUI "Enable Dear ImGui (GLFW+OpenGL3 backend)" ON)
if(ENABLE_IMGUI)
  FetchContent_Declare(
    imgui
    GIT_REPOSITORY https://github.com/ocornut/imgui.git
    GIT_TAG v1.91.0
  )
  FetchContent_MakeAvailable(imgui)

  # 使用拉取到的源码目录组装一个本地目标
  set(IMGUI_DIR ${imgui_SOURCE_DIR})
  add_library(imgui STATIC
    ${IMGUI_DIR}/imgui.cpp
    ${IMGUI_DIR}/imgui_draw.cpp
    ${IMGUI_DIR}/imgui_tables.cpp
    ${IMGUI_DIR}/imgui_widgets.cpp
    ${IMGUI_DIR}/backends/imgui_impl_glfw.cpp
    ${IMGUI_DIR}/backends/imgui_impl_opengl3.cpp
  )
  target_include_directories(imgui PUBLIC
    ${IMGUI_DIR}
    ${IMGUI_DIR}/backends
  )
  # 使用 GLAD 作为 OpenGL loader
  target_compile_definitions(imgui PUBLIC IMGUI_IMPL_OPENGL_LOADER_GLAD)
  target_link_libraries(imgui PUBLIC
    ${GLFW_TARGET}
    glad_opengl
    OpenGL::GL
  )
endif()

# 4) 手动配置 GLAD
set(GLAD_INCLUDE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/include)
set(GLAD_SRC ${CMAKE_CURRENT_SOURCE_DIR}/src/glad.c)

# 创建 GLAD 库
add_library(glad_opengl STATIC ${GLAD_SRC})
target_include_directories(glad_opengl PUBLIC ${GLAD_INCLUDE_DIR})
target_compile_definitions(glad_opengl PUBLIC GLAD_GL_IMPLEMENTATION)

# 5) 收集应用程序源文件
file(GLOB_RECURSE APP_SOURCES
  CONFIGURE_DEPENDS
  ${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp
  # 排除 glad.c，因为它已经包含在 glad_opengl 库中
)

# 创建可执行文件
add_executable(cg_app ${APP_SOURCES})

# 包含目录
target_include_directories(cg_app PRIVATE
  ${CMAKE_CURRENT_SOURCE_DIR}/include
  ${GLAD_INCLUDE_DIR}
  $<$<BOOL:${ENABLE_IMGUI}>:${IMGUI_DIR}>
  $<$<BOOL:${ENABLE_IMGUI}>:${IMGUI_DIR}/backends>
)

# 避免 GLFW 自动包含 OpenGL 头，由 GLAD 统一处理
target_compile_definitions(cg_app PRIVATE GLFW_INCLUDE_NONE)
# 若源码里也包含了 ImGui backend 头文件，确保定义同样的 loader 宏
if(ENABLE_IMGUI)
  target_compile_definitions(cg_app PRIVATE IMGUI_IMPL_OPENGL_LOADER_GLAD)
endif()
# GLM 统一使用弧度
target_compile_definitions(cg_app PRIVATE GLM_FORCE_RADIANS)

# 链接依赖
target_link_libraries(cg_app PRIVATE
  OpenGL::GL
  ${GLFW_TARGET}
  glad_opengl
  glm::glm
  $<$<BOOL:${ENABLE_IMGUI}>:imgui>
)

# Windows/MSVC 特定设置
if(WIN32)
  # 链接 Windows 库
  target_link_libraries(cg_app PRIVATE
    kernel32
    user32
    gdi32
    winspool
    shell32
    ole32
    oleaut32
    uuid
    comdlg32
    advapi32
  )
endif()

# 编译器警告设置
if(MSVC)
  target_compile_options(cg_app PRIVATE /W4 /permissive-)
else()
  target_compile_options(cg_app PRIVATE -Wall -Wextra -Wpedantic)
endif()

# 运行时工作目录（VS 用户可用，便于加载资源）
set_property(TARGET cg_app PROPERTY VS_DEBUGGER_WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})

# 添加安装目标（可选）
install(TARGETS cg_app
  RUNTIME DESTINATION bin
  LIBRARY DESTINATION lib
  ARCHIVE DESTINATION lib
)

# 自动将 assets 文件夹复制到构建目录，这样程序运行就能找到图片了
if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/assets)
  file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/assets DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
endif()