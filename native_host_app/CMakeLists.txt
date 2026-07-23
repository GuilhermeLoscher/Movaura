cmake_minimum_required(VERSION 3.20)

project(movaura_host_probe LANGUAGES CXX)

set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

add_executable(movaura_host_probe
    src/main.cpp
)

target_compile_features(movaura_host_probe PRIVATE cxx_std_17)
target_link_libraries(movaura_host_probe PRIVATE Shell32)

if(MSVC)
    target_compile_options(movaura_host_probe PRIVATE /W4 /permissive-)
else()
    target_compile_options(movaura_host_probe PRIVATE -Wall -Wextra)
endif()

set_target_properties(movaura_host_probe PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)
