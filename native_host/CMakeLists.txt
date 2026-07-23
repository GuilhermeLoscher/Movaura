cmake_minimum_required(VERSION 3.20)

project(movaura_native_host LANGUAGES CXX)

set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

add_library(movaura_native_host SHARED
    src/movaura_native_host.cpp
)

target_compile_features(movaura_native_host PRIVATE cxx_std_17)
target_include_directories(movaura_native_host PUBLIC include)
target_compile_definitions(movaura_native_host PRIVATE MOVAURA_NATIVE_HOST_EXPORTS)

if(MSVC)
    target_compile_options(movaura_native_host PRIVATE /W4 /permissive-)
else()
    target_compile_options(movaura_native_host PRIVATE -Wall -Wextra)
endif()

set_target_properties(movaura_native_host PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
    ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
)
