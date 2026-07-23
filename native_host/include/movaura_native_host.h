#pragma once

#include <cstdint>

#ifdef _WIN32
#ifdef MOVAURA_NATIVE_HOST_EXPORTS
#define NW_API __declspec(dllexport)
#else
#define NW_API __declspec(dllimport)
#endif
#else
#define NW_API
#endif

extern "C" {

struct NwWindowInfo {
    std::uint64_t hwnd;
    std::uint32_t pid;
    std::int32_t left;
    std::int32_t top;
    std::int32_t right;
    std::int32_t bottom;
    std::int32_t visible;
};

struct NwDesktopReport {
    NwWindowInfo progman;
    NwWindowInfo shell_defview;
    NwWindowInfo sys_listview;
    NwWindowInfo workerw_with_defview;
    NwWindowInfo workerw_after_defview;
    NwWindowInfo wallpaper_workerw;
    std::int32_t workerw_count;
    std::int32_t send_ok;
    std::uint64_t last_error;
};

struct NwAttachResult {
    std::int32_t success;
    std::uint64_t parent_hwnd;
    std::uint64_t last_error;
};

NW_API std::int32_t nw_probe_desktop(NwDesktopReport* report);
NW_API std::int32_t nw_attach_to_workerw_after_defview(
    std::uint64_t child_hwnd,
    std::int32_t x,
    std::int32_t y,
    std::int32_t width,
    std::int32_t height,
    NwAttachResult* result
);
NW_API std::int32_t nw_attach_to_progman_stack(
    std::uint64_t child_hwnd,
    std::int32_t x,
    std::int32_t y,
    std::int32_t width,
    std::int32_t height,
    NwAttachResult* result
);
NW_API std::int32_t nw_send_workerw_messages();

}
