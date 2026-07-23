#include "movaura_native_host.h"

#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>

#include <algorithm>
#include <cwchar>
#include <iterator>
#include <vector>

namespace {

constexpr UINT kSpawnWorkerW = 0x052C;

struct EnumContext {
    std::vector<HWND>* windows;
    const wchar_t* class_name;
};

BOOL CALLBACK EnumTopLevelByClass(HWND hwnd, LPARAM lparam) {
    auto* context = reinterpret_cast<EnumContext*>(lparam);
    wchar_t class_name[128] = {};
    GetClassNameW(hwnd, class_name, static_cast<int>(std::size(class_name)));
    if (wcscmp(class_name, context->class_name) == 0) {
        context->windows->push_back(hwnd);
    }
    return TRUE;
}

HWND FindChildDeep(HWND parent, const wchar_t* class_name) {
    if (!parent) {
        return nullptr;
    }

    HWND direct = FindWindowExW(parent, nullptr, class_name, nullptr);
    if (direct) {
        return direct;
    }

    struct ChildContext {
        const wchar_t* class_name;
        HWND found;
    } context{class_name, nullptr};

    EnumChildWindows(
        parent,
        [](HWND child, LPARAM lparam) -> BOOL {
            auto* context = reinterpret_cast<ChildContext*>(lparam);
            wchar_t child_class[128] = {};
            GetClassNameW(child, child_class, static_cast<int>(std::size(child_class)));
            if (wcscmp(child_class, context->class_name) == 0) {
                context->found = child;
                return FALSE;
            }
            return TRUE;
        },
        reinterpret_cast<LPARAM>(&context)
    );

    return context.found;
}

std::vector<HWND> FindTopLevelByClass(const wchar_t* class_name) {
    std::vector<HWND> windows;
    EnumContext context{&windows, class_name};
    EnumWindows(EnumTopLevelByClass, reinterpret_cast<LPARAM>(&context));
    return windows;
}

DWORD PidOf(HWND hwnd) {
    DWORD pid = 0;
    if (hwnd) {
        GetWindowThreadProcessId(hwnd, &pid);
    }
    return pid;
}

int AreaOf(HWND hwnd) {
    RECT rect{};
    if (!hwnd || !GetWindowRect(hwnd, &rect)) {
        return 0;
    }
    LONG width = std::max(0L, rect.right - rect.left);
    LONG height = std::max(0L, rect.bottom - rect.top);
    return static_cast<int>(width * height);
}

NwWindowInfo ToInfo(HWND hwnd) {
    NwWindowInfo info{};
    info.hwnd = reinterpret_cast<std::uint64_t>(hwnd);
    info.pid = PidOf(hwnd);
    info.visible = hwnd && IsWindowVisible(hwnd) ? 1 : 0;

    RECT rect{};
    if (hwnd && GetWindowRect(hwnd, &rect)) {
        info.left = rect.left;
        info.top = rect.top;
        info.right = rect.right;
        info.bottom = rect.bottom;
    }

    return info;
}

HWND FindWorkerWWithDefView(const std::vector<HWND>& workerws) {
    for (HWND workerw : workerws) {
        if (FindChildDeep(workerw, L"SHELLDLL_DefView")) {
            return workerw;
        }
    }
    return nullptr;
}

HWND FindWorkerWAfterDefView(HWND progman, HWND shell_defview, HWND workerw_with_defview) {
    if (progman && shell_defview && GetParent(shell_defview) == progman) {
        HWND child_candidate = FindWindowExW(progman, shell_defview, L"WorkerW", nullptr);
        while (child_candidate) {
            if (
                PidOf(child_candidate) == PidOf(progman)
                && AreaOf(child_candidate) >= 200000
                && !FindChildDeep(child_candidate, L"SHELLDLL_DefView")
            ) {
                return child_candidate;
            }
            child_candidate = FindWindowExW(progman, child_candidate, L"WorkerW", nullptr);
        }
    }

    HWND owner = workerw_with_defview ? workerw_with_defview : progman;
    if (!owner) {
        return nullptr;
    }

    HWND candidate = FindWindowExW(nullptr, owner, L"WorkerW", nullptr);
    while (candidate) {
        if (!FindChildDeep(candidate, L"SHELLDLL_DefView")) {
            return candidate;
        }
        candidate = FindWindowExW(nullptr, candidate, L"WorkerW", nullptr);
    }
    return nullptr;
}

HWND FindValidatedWallpaperWorkerW(HWND progman, const std::vector<HWND>& workerws) {
    DWORD explorer_pid = PidOf(progman);
    HWND best = nullptr;
    int best_area = 0;

    for (HWND workerw : workerws) {
        if (FindChildDeep(workerw, L"SHELLDLL_DefView")) {
            continue;
        }
        if (PidOf(workerw) != explorer_pid) {
            continue;
        }

        int area = AreaOf(workerw);
        if (area < 200000) {
            continue;
        }
        if (area > best_area) {
            best = workerw;
            best_area = area;
        }
    }

    return best;
}

bool SendWorkerWMessage(HWND progman, WPARAM wparam, LPARAM lparam) {
    DWORD_PTR result = 0;
    return SendMessageTimeoutW(
               progman,
               kSpawnWorkerW,
               wparam,
               lparam,
               SMTO_NORMAL,
               1000,
               &result
           ) != 0;
}

bool PrepareChildWallpaper(HWND hwnd) {
    LONG_PTR style = GetWindowLongPtrW(hwnd, GWL_STYLE);
    style &= ~WS_POPUP;
    style &= ~WS_CAPTION;
    style &= ~WS_THICKFRAME;
    style |= WS_CHILD;
    style |= WS_VISIBLE;
    SetLastError(0);
    if (!SetWindowLongPtrW(hwnd, GWL_STYLE, style)) {
        return GetLastError() == 0;
    }

    LONG_PTR ex_style = GetWindowLongPtrW(hwnd, GWL_EXSTYLE);
    ex_style &= ~WS_EX_APPWINDOW;
    ex_style |= WS_EX_TOOLWINDOW;
    SetLastError(0);
    if (!SetWindowLongPtrW(hwnd, GWL_EXSTYLE, ex_style)) {
        return GetLastError() == 0;
    }

    return true;
}

}  // namespace

extern "C" {

NW_API std::int32_t nw_send_workerw_messages() {
    HWND progman = FindWindowW(L"Progman", L"Program Manager");
    if (!progman) {
        return 0;
    }

    int sent = 0;
    sent += SendWorkerWMessage(progman, 0, 0) ? 1 : 0;
    sent += SendWorkerWMessage(progman, 0xD, 0) ? 1 : 0;
    sent += SendWorkerWMessage(progman, 0xD, 1) ? 1 : 0;
    sent += SendWorkerWMessage(progman, 0, 0) ? 1 : 0;
    return sent;
}

NW_API std::int32_t nw_probe_desktop(NwDesktopReport* report) {
    if (!report) {
        return 0;
    }

    *report = NwDesktopReport{};
    SetLastError(0);

    HWND progman = FindWindowW(L"Progman", L"Program Manager");
    report->progman = ToInfo(progman);
    if (!progman) {
        report->last_error = GetLastError();
        return 0;
    }

    report->send_ok = nw_send_workerw_messages() > 0 ? 1 : 0;

    std::vector<HWND> workerws = FindTopLevelByClass(L"WorkerW");
    report->workerw_count = static_cast<std::int32_t>(workerws.size());
    HWND workerw_with_defview = FindWorkerWWithDefView(workerws);
    HWND shell_defview = FindChildDeep(progman, L"SHELLDLL_DefView");
    if (!shell_defview && workerw_with_defview) {
        shell_defview = FindChildDeep(workerw_with_defview, L"SHELLDLL_DefView");
    }

    HWND sys_listview = shell_defview ? FindChildDeep(shell_defview, L"SysListView32") : nullptr;
    HWND workerw_after_defview = FindWorkerWAfterDefView(progman, shell_defview, workerw_with_defview);
    HWND wallpaper_workerw = workerw_after_defview ? workerw_after_defview
                                                   : FindValidatedWallpaperWorkerW(progman, workerws);

    report->shell_defview = ToInfo(shell_defview);
    report->sys_listview = ToInfo(sys_listview);
    report->workerw_with_defview = ToInfo(workerw_with_defview);
    report->workerw_after_defview = ToInfo(workerw_after_defview);
    report->wallpaper_workerw = ToInfo(wallpaper_workerw);
    report->last_error = GetLastError();
    return 1;
}

NW_API std::int32_t nw_attach_to_workerw_after_defview(
    std::uint64_t child_hwnd,
    std::int32_t x,
    std::int32_t y,
    std::int32_t width,
    std::int32_t height,
    NwAttachResult* result
) {
    if (!result) {
        return 0;
    }

    *result = NwAttachResult{};
    HWND child = reinterpret_cast<HWND>(child_hwnd);
    if (!child || !IsWindow(child)) {
        result->last_error = ERROR_INVALID_WINDOW_HANDLE;
        return 0;
    }

    NwDesktopReport report{};
    if (!nw_probe_desktop(&report) || !report.workerw_after_defview.hwnd) {
        result->last_error = ERROR_NOT_FOUND;
        return 0;
    }

    HWND parent = reinterpret_cast<HWND>(report.workerw_after_defview.hwnd);
    RECT parent_rect{};
    GetWindowRect(parent, &parent_rect);

    int child_x = x - parent_rect.left;
    int child_y = y - parent_rect.top;

    if (!PrepareChildWallpaper(child)) {
        result->last_error = GetLastError();
        return 0;
    }

    SetParent(child, parent);
    MoveWindow(child, child_x, child_y, width, height, TRUE);
    SetWindowPos(
        child,
        HWND_BOTTOM,
        0,
        0,
        0,
        0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
    );

    result->parent_hwnd = reinterpret_cast<std::uint64_t>(parent);
    result->success = GetParent(child) == parent ? 1 : 0;
    result->last_error = GetLastError();
    return result->success;
}

NW_API std::int32_t nw_attach_to_progman_stack(
    std::uint64_t child_hwnd,
    std::int32_t x,
    std::int32_t y,
    std::int32_t width,
    std::int32_t height,
    NwAttachResult* result
) {
    if (!result) {
        return 0;
    }

    *result = NwAttachResult{};
    HWND child = reinterpret_cast<HWND>(child_hwnd);
    if (!child || !IsWindow(child)) {
        result->last_error = ERROR_INVALID_WINDOW_HANDLE;
        return 0;
    }

    NwDesktopReport report{};
    if (!nw_probe_desktop(&report) || !report.progman.hwnd || !report.shell_defview.hwnd) {
        result->last_error = ERROR_NOT_FOUND;
        return 0;
    }

    HWND progman = reinterpret_cast<HWND>(report.progman.hwnd);
    HWND shell_defview = reinterpret_cast<HWND>(report.shell_defview.hwnd);
    if (GetParent(shell_defview) != progman) {
        result->last_error = ERROR_NOT_SUPPORTED;
        return 0;
    }

    RECT parent_rect{};
    GetWindowRect(progman, &parent_rect);
    int child_x = x - parent_rect.left;
    int child_y = y - parent_rect.top;

    if (!PrepareChildWallpaper(child)) {
        result->last_error = GetLastError();
        return 0;
    }

    SetLastError(0);
    SetParent(child, progman);
    if (GetParent(child) != progman) {
        result->last_error = GetLastError();
        return 0;
    }

    BOOL wallpaper_positioned = SetWindowPos(
        child,
        HWND_BOTTOM,
        child_x,
        child_y,
        width,
        height,
        SWP_SHOWWINDOW | SWP_NOACTIVATE | SWP_FRAMECHANGED
    );
    BOOL icons_positioned = SetWindowPos(
        shell_defview,
        HWND_TOP,
        0,
        0,
        0,
        0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
    );

    result->parent_hwnd = reinterpret_cast<std::uint64_t>(progman);
    result->success = wallpaper_positioned && icons_positioned ? 1 : 0;
    result->last_error = GetLastError();
    return result->success;
}

}
