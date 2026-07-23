cmake_minimum_required(VERSION 3.20)

project(movaura_native_compositor LANGUAGES CXX)

set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

add_executable(movaura_native_compositor WIN32
    src/main.cpp
)

target_compile_features(movaura_native_compositor PRIVATE cxx_std_17)
target_link_libraries(movaura_native_compositor PRIVATE
    D2d1
    D3d11
    Dcomp
    Dxgi
    Mf
    Mfplat
    Mfreadwrite
    Mfuuid
    Shell32
    Windowscodecs
    Ole32
    Winmm
)

if(MSVC)
    target_compile_options(movaura_native_compositor PRIVATE /W4 /permissive-)
else()
    target_compile_options(movaura_native_compositor PRIVATE -Wall -Wextra)
endif()

set_target_properties(movaura_native_compositor PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
    OUTPUT_NAME "movaura_native_compositor"
)
