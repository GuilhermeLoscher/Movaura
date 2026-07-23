#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <shellapi.h>

#include <algorithm>
#include <cwchar>
#include <sstream>
#include <string>
#include <vector>

namespace {

constexpr UINT kSpawnWorkerW = 0x052C;
constexpr wchar_t kWindowClass[] = L"MovauraNativeHostProbe";
constexpr UINT kListViewFirst = 0x1000;
constexpr UINT kListViewGetBkColor = kListViewFirst;
constexpr UINT kListViewSetBkColor = kListViewFirst + 1;
constexpr UINT kListViewGetTextBkColor = kListViewFirst + 37;
constexpr UINT kListViewSetTextBkColor = kListViewFirst + 38;
constexpr COLORREF kTransparentColor = 0xFFFFFFFF;

HWND g_transparent_listview = nullptr;
COLORREF g_previous_listview_background = CLR_INVALID;
COLORREF g_previous_listview_text_background = CLR_INVALID;
HWND g_reparented_shell_defview = nullptr;
HWND g_original_shell_parent = nullptr;
RECT g_original_shell_rect{};
HWND g_reparented_listview = nullptr;
HWND g_original_listview_parent = nullptr;
RECT g_original_listview_rect{};

struct DesktopTopology {
    HWND progman = nullptr;
    HWND shell_defview = nullptr;
    HWND sys_listview = nullptr;
    HWND workerw_with_defview = nullptr;
    HWND workerw_after_defview = nullptr;
    HWND wallpaper_workerw = nullptr;
    std::vector<HWND> workerws;
};

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

std::vector<HWND> FindTopLevelByClass(const wchar_t* class_name) {
    std::vector<HWND> windows;
    EnumContext context{&windows, class_name};
    EnumWindows(EnumTopLevelByClass, reinterpret_cast<LPARAM>(&context));
    return windows;
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

std::wstring WindowSummary(HWND hwnd) {
    if (!hwnd) {
        return L"not found";
    }

    RECT rect{};
    GetWindowRect(hwnd, &rect);
    wchar_t class_name[128] = {};
    GetClassNameW(hwnd, class_name, static_cast<int>(std::size(class_name)));

    std::wstringstream stream;
    stream << L"hwnd=" << reinterpret_cast<std::uintptr_t>(hwnd)
           << L" class=" << class_name
           << L" pid=" << PidOf(hwnd)
           << L" visible=" << (IsWindowVisible(hwnd) ? L"true" : L"false")
           << L" rect=(" << rect.left << L"," << rect.top << L"," << rect.right << L"," << rect.bottom << L")"
           << L" size=" << (rect.right - rect.left) << L"x" << (rect.bottom - rect.top);
    return stream.str();
}

void PrintLine(const std::wstring& text) {
    DWORD written = 0;
    HANDLE out = GetStdHandle(STD_OUTPUT_HANDLE);
    std::wstring line = text + L"\r\n";
    DWORD mode = 0;
    if (GetConsoleMode(out, &mode)) {
        WriteConsoleW(out, line.c_str(), static_cast<DWORD>(line.size()), &written, nullptr);
        return;
    }

    int byte_count = WideCharToMultiByte(
        CP_UTF8,
        0,
        line.c_str(),
        static_cast<int>(line.size()),
        nullptr,
        0,
        nullptr,
        nullptr
    );
    if (byte_count <= 0) {
        return;
    }

    std::string utf8(static_cast<size_t>(byte_count), '\0');
    WideCharToMultiByte(
        CP_UTF8,
        0,
        line.c_str(),
        static_cast<int>(line.size()),
        utf8.data(),
        byte_count,
        nullptr,
        nullptr
    );
    WriteFile(out, utf8.data(), static_cast<DWORD>(utf8.size()), &written, nullptr);
}

void PrintLastError(const std::wstring& operation, bool ok) {
    std::wstringstream stream;
    stream << operation << L": " << (ok ? L"ok" : L"failed")
           << L" last_error=" << GetLastError();
    PrintLine(stream.str());
}

void EnsureConsole() {
    if (GetConsoleWindow()) {
        return;
    }
    if (!AttachConsole(ATTACH_PARENT_PROCESS)) {
        AllocConsole();
    }
    FILE* ignored = nullptr;
    freopen_s(&ignored, "CONOUT$", "w", stdout);
    freopen_s(&ignored, "CONOUT$", "w", stderr);
}

void SendWorkerWMessages(HWND progman) {
    const std::pair<WPARAM, LPARAM> messages[] = {
        {0, 0},
        {0xD, 0},
        {0xD, 1},
        {0, 0},
    };

    for (auto [wparam, lparam] : messages) {
        DWORD_PTR result = 0;
        BOOL ok = SendMessageTimeoutW(
            progman,
            kSpawnWorkerW,
            wparam,
            lparam,
            SMTO_NORMAL,
            1000,
            &result
        ) != 0;
        std::wstringstream stream;
        stream << L"0x052C wParam=" << wparam << L" lParam=" << lparam
               << L" ok=" << (ok ? L"true" : L"false") << L" result=" << result;
        PrintLine(stream.str());
    }
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

DesktopTopology ProbeDesktop() {
    DesktopTopology topology;
    topology.progman = FindWindowW(L"Progman", L"Program Manager");
    if (topology.progman) {
        SendWorkerWMessages(topology.progman);
    }

    topology.workerws = FindTopLevelByClass(L"WorkerW");
    topology.workerw_with_defview = FindWorkerWWithDefView(topology.workerws);
    topology.shell_defview = FindChildDeep(topology.progman, L"SHELLDLL_DefView");
    if (!topology.shell_defview && topology.workerw_with_defview) {
        topology.shell_defview = FindChildDeep(topology.workerw_with_defview, L"SHELLDLL_DefView");
    }
    topology.sys_listview = FindChildDeep(topology.shell_defview, L"SysListView32");
    topology.workerw_after_defview = FindWorkerWAfterDefView(
        topology.progman,
        topology.shell_defview,
        topology.workerw_with_defview
    );
    topology.wallpaper_workerw = topology.workerw_after_defview
                                      ? topology.workerw_after_defview
                                      : FindValidatedWallpaperWorkerW(topology.progman, topology.workerws);
    return topology;
}

void PrintTopology(const DesktopTopology& topology) {
    PrintLine(L"Movaura native host app diagnostics:");
    PrintLine(L"Progman: " + WindowSummary(topology.progman));
    PrintLine(L"SHELLDLL_DefView: " + WindowSummary(topology.shell_defview));
    PrintLine(L"SysListView32: " + WindowSummary(topology.sys_listview));
    PrintLine(L"WorkerW with DefView: " + WindowSummary(topology.workerw_with_defview));
    PrintLine(L"WorkerW after DefView: " + WindowSummary(topology.workerw_after_defview));
    PrintLine(L"Wallpaper WorkerW: " + WindowSummary(topology.wallpaper_workerw));
    PrintLine(L"WorkerW count: " + std::to_wstring(topology.workerws.size()));

    for (size_t index = 0; index < topology.workerws.size(); ++index) {
        PrintLine(L"  WorkerW[" + std::to_wstring(index + 1) + L"]: " + WindowSummary(topology.workerws[index]));
    }
}

void PrintDirectChildren(const std::wstring& label, HWND parent) {
    PrintLine(label + L" direct children:");
    if (!parent) {
        PrintLine(L"  parent not found");
        return;
    }

    HWND child = GetWindow(parent, GW_CHILD);
    if (!child) {
        PrintLine(L"  none");
        return;
    }

    size_t index = 1;
    while (child) {
        PrintLine(L"  [" + std::to_wstring(index++) + L"] " + WindowSummary(child));
        child = GetWindow(child, GW_HWNDNEXT);
    }
}

RECT PrimaryMonitorRect() {
    return RECT{0, 0, GetSystemMetrics(SM_CXSCREEN), GetSystemMetrics(SM_CYSCREEN)};
}

bool PrepareChild(HWND hwnd) {
    LONG_PTR style = GetWindowLongPtrW(hwnd, GWL_STYLE);
    style &= ~WS_POPUP;
    style &= ~WS_CAPTION;
    style &= ~WS_THICKFRAME;
    style |= WS_CHILD | WS_VISIBLE;
    SetWindowLongPtrW(hwnd, GWL_STYLE, style);

    LONG_PTR ex_style = GetWindowLongPtrW(hwnd, GWL_EXSTYLE);
    ex_style &= ~WS_EX_APPWINDOW;
    ex_style |= WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE | WS_EX_TRANSPARENT;
    SetWindowLongPtrW(hwnd, GWL_EXSTYLE, ex_style);
    return true;
}

void AttachChild(HWND child, HWND parent, RECT monitor_rect, bool top) {
    RECT parent_rect{};
    GetWindowRect(parent, &parent_rect);
    int x = monitor_rect.left - parent_rect.left;
    int y = monitor_rect.top - parent_rect.top;
    int width = monitor_rect.right - monitor_rect.left;
    int height = monitor_rect.bottom - monitor_rect.top;

    PrepareChild(child);
    SetParent(child, parent);
    MoveWindow(child, x, y, width, height, TRUE);
    SetWindowPos(
        child,
        top ? HWND_TOP : HWND_BOTTOM,
        x,
        y,
        width,
        height,
        SWP_SHOWWINDOW | SWP_NOACTIVATE | SWP_FRAMECHANGED
    );
}

bool AttachProgmanStack(HWND child, const DesktopTopology& topology, RECT monitor_rect) {
    if (!child || !topology.progman || !topology.shell_defview) {
        PrintLine(L"progman-stack mode failed: missing child, Progman, or SHELLDLL_DefView.");
        return false;
    }

    RECT parent_rect{};
    GetWindowRect(topology.progman, &parent_rect);
    int x = monitor_rect.left - parent_rect.left;
    int y = monitor_rect.top - parent_rect.top;
    int width = monitor_rect.right - monitor_rect.left;
    int height = monitor_rect.bottom - monitor_rect.top;

    PrepareChild(child);
    SetLastError(ERROR_SUCCESS);
    HWND previous_parent = SetParent(child, topology.progman);
    PrintLastError(L"progman-stack SetParent", previous_parent != nullptr || GetLastError() == ERROR_SUCCESS);

    SetLastError(ERROR_SUCCESS);
    BOOL positioned = SetWindowPos(
        child,
        HWND_BOTTOM,
        x,
        y,
        width,
        height,
        SWP_SHOWWINDOW | SWP_NOACTIVATE | SWP_FRAMECHANGED
    );
    PrintLastError(L"progman-stack wallpaper HWND_BOTTOM", positioned != FALSE);

    SetLastError(ERROR_SUCCESS);
    BOOL icons_above = SetWindowPos(
        topology.shell_defview,
        HWND_TOP,
        0,
        0,
        0,
        0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
    );
    PrintLastError(L"progman-stack SHELLDLL_DefView HWND_TOP", icons_above != FALSE);

    ShowWindow(child, SW_SHOWNOACTIVATE);
    InvalidateRect(child, nullptr, TRUE);
    UpdateWindow(child);
    PrintLine(L"progman-stack wallpaper: " + WindowSummary(child));
    PrintLine(L"progman-stack icon layer: " + WindowSummary(topology.shell_defview));
    return positioned != FALSE && icons_above != FALSE;
}

void RestoreTransparentIconLayer() {
    if (!g_transparent_listview || !IsWindow(g_transparent_listview)) {
        return;
    }

    if (g_previous_listview_background != CLR_INVALID) {
        SendMessageW(
            g_transparent_listview,
            kListViewSetBkColor,
            0,
            static_cast<LPARAM>(g_previous_listview_background)
        );
    }
    if (g_previous_listview_text_background != CLR_INVALID) {
        SendMessageW(
            g_transparent_listview,
            kListViewSetTextBkColor,
            0,
            static_cast<LPARAM>(g_previous_listview_text_background)
        );
    }
    InvalidateRect(g_transparent_listview, nullptr, TRUE);
    g_transparent_listview = nullptr;
}

void RestoreShellStack() {
    if (!g_reparented_shell_defview || !IsWindow(g_reparented_shell_defview)) {
        return;
    }

    if (g_original_shell_parent && IsWindow(g_original_shell_parent)) {
        SetParent(g_reparented_shell_defview, g_original_shell_parent);
        SetWindowPos(
            g_reparented_shell_defview,
            HWND_TOP,
            g_original_shell_rect.left,
            g_original_shell_rect.top,
            g_original_shell_rect.right - g_original_shell_rect.left,
            g_original_shell_rect.bottom - g_original_shell_rect.top,
            SWP_SHOWWINDOW | SWP_NOACTIVATE | SWP_FRAMECHANGED
        );
    }

    g_reparented_shell_defview = nullptr;
    g_original_shell_parent = nullptr;
    g_original_shell_rect = {};
}

void RestoreListViewStack() {
    if (!g_reparented_listview || !IsWindow(g_reparented_listview)) {
        return;
    }

    if (g_original_listview_parent && IsWindow(g_original_listview_parent)) {
        SetParent(g_reparented_listview, g_original_listview_parent);
        SetWindowPos(
            g_reparented_listview,
            HWND_TOP,
            g_original_listview_rect.left,
            g_original_listview_rect.top,
            g_original_listview_rect.right - g_original_listview_rect.left,
            g_original_listview_rect.bottom - g_original_listview_rect.top,
            SWP_SHOWWINDOW | SWP_NOACTIVATE | SWP_FRAMECHANGED
        );
    }

    g_reparented_listview = nullptr;
    g_original_listview_parent = nullptr;
    g_original_listview_rect = {};
}

BOOL WINAPI ConsoleControlHandler(DWORD control_type) {
    if (control_type == CTRL_C_EVENT || control_type == CTRL_BREAK_EVENT || control_type == CTRL_CLOSE_EVENT) {
        RestoreTransparentIconLayer();
        RestoreListViewStack();
        RestoreShellStack();
    }
    return FALSE;
}

bool AttachWorkerWShellStack(HWND child, const DesktopTopology& topology, RECT monitor_rect) {
    if (!child || !topology.progman || !topology.shell_defview || !topology.workerw_after_defview) {
        PrintLine(L"workerw-shell-stack mode failed: missing child, Progman, SHELLDLL_DefView, or WorkerW.");
        return false;
    }

    g_reparented_shell_defview = topology.shell_defview;
    g_original_shell_parent = GetParent(topology.shell_defview);
    GetWindowRect(topology.shell_defview, &g_original_shell_rect);
    MapWindowPoints(
        HWND_DESKTOP,
        g_original_shell_parent,
        reinterpret_cast<POINT*>(&g_original_shell_rect),
        2
    );
    SetConsoleCtrlHandler(ConsoleControlHandler, TRUE);

    RECT worker_rect{};
    GetClientRect(topology.workerw_after_defview, &worker_rect);
    SetLastError(ERROR_SUCCESS);
    HWND previous_parent = SetParent(topology.shell_defview, topology.workerw_after_defview);
    PrintLastError(
        L"workerw-shell-stack SHELLDLL_DefView SetParent",
        previous_parent != nullptr || GetLastError() == ERROR_SUCCESS
    );

    AttachChild(child, topology.workerw_after_defview, monitor_rect, false);
    BOOL icons_above = SetWindowPos(
        topology.shell_defview,
        HWND_TOP,
        0,
        0,
        worker_rect.right - worker_rect.left,
        worker_rect.bottom - worker_rect.top,
        SWP_SHOWWINDOW | SWP_NOACTIVATE | SWP_FRAMECHANGED
    );
    PrintLastError(L"workerw-shell-stack SHELLDLL_DefView HWND_TOP", icons_above != FALSE);
    PrintLine(L"workerw-shell-stack wallpaper: " + WindowSummary(child));
    PrintLine(L"workerw-shell-stack icon layer: " + WindowSummary(topology.shell_defview));
    return icons_above != FALSE;
}

bool AttachWorkerWListViewStack(HWND child, const DesktopTopology& topology, RECT monitor_rect) {
    if (!child || !topology.sys_listview || !topology.workerw_after_defview) {
        PrintLine(L"workerw-listview-stack mode failed: missing child, SysListView32, or WorkerW.");
        return false;
    }

    g_reparented_listview = topology.sys_listview;
    g_original_listview_parent = GetParent(topology.sys_listview);
    GetWindowRect(topology.sys_listview, &g_original_listview_rect);
    MapWindowPoints(
        HWND_DESKTOP,
        g_original_listview_parent,
        reinterpret_cast<POINT*>(&g_original_listview_rect),
        2
    );
    SetConsoleCtrlHandler(ConsoleControlHandler, TRUE);

    RECT worker_rect{};
    GetClientRect(topology.workerw_after_defview, &worker_rect);
    SetLastError(ERROR_SUCCESS);
    HWND previous_parent = SetParent(topology.sys_listview, topology.workerw_after_defview);
    PrintLastError(
        L"workerw-listview-stack SysListView32 SetParent",
        previous_parent != nullptr || GetLastError() == ERROR_SUCCESS
    );

    AttachChild(child, topology.workerw_after_defview, monitor_rect, false);
    BOOL icons_above = SetWindowPos(
        topology.sys_listview,
        HWND_TOP,
        0,
        0,
        worker_rect.right - worker_rect.left,
        worker_rect.bottom - worker_rect.top,
        SWP_SHOWWINDOW | SWP_NOACTIVATE | SWP_FRAMECHANGED
    );
    PrintLastError(L"workerw-listview-stack SysListView32 HWND_TOP", icons_above != FALSE);
    PrintLine(L"workerw-listview-stack wallpaper: " + WindowSummary(child));
    PrintLine(L"workerw-listview-stack icon layer: " + WindowSummary(topology.sys_listview));
    return icons_above != FALSE;
}

bool AttachDefViewTransparentIcons(HWND child, const DesktopTopology& topology, RECT monitor_rect) {
    if (!child || !topology.shell_defview || !topology.sys_listview) {
        PrintLine(L"defview-transparent-icons mode failed: missing child, SHELLDLL_DefView, or SysListView32.");
        return false;
    }

    RECT parent_rect{};
    GetWindowRect(topology.shell_defview, &parent_rect);
    int x = monitor_rect.left - parent_rect.left;
    int y = monitor_rect.top - parent_rect.top;
    int width = monitor_rect.right - monitor_rect.left;
    int height = monitor_rect.bottom - monitor_rect.top;

    g_transparent_listview = topology.sys_listview;
    g_previous_listview_background = static_cast<COLORREF>(
        SendMessageW(g_transparent_listview, kListViewGetBkColor, 0, 0)
    );
    g_previous_listview_text_background = static_cast<COLORREF>(
        SendMessageW(g_transparent_listview, kListViewGetTextBkColor, 0, 0)
    );
    SetConsoleCtrlHandler(ConsoleControlHandler, TRUE);

    std::wstringstream colors;
    colors << L"listview colors before: background=0x" << std::hex << g_previous_listview_background
           << L" text_background=0x" << g_previous_listview_text_background;
    PrintLine(colors.str());

    SendMessageW(g_transparent_listview, kListViewSetBkColor, 0, static_cast<LPARAM>(kTransparentColor));
    SendMessageW(g_transparent_listview, kListViewSetTextBkColor, 0, static_cast<LPARAM>(kTransparentColor));

    PrepareChild(child);
    SetParent(child, topology.shell_defview);
    BOOL positioned = SetWindowPos(
        child,
        HWND_BOTTOM,
        x,
        y,
        width,
        height,
        SWP_SHOWWINDOW | SWP_NOACTIVATE | SWP_FRAMECHANGED
    );
    SetWindowPos(
        topology.sys_listview,
        HWND_TOP,
        0,
        0,
        0,
        0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
    );
    InvalidateRect(topology.sys_listview, nullptr, TRUE);
    InvalidateRect(child, nullptr, TRUE);
    UpdateWindow(child);
    PrintLastError(L"defview-transparent-icons wallpaper HWND_BOTTOM", positioned != FALSE);
    PrintLine(L"defview-transparent-icons wallpaper: " + WindowSummary(child));
    return positioned != FALSE;
}

void AttachTopLevel(HWND child, RECT monitor_rect, bool topmost) {
    SetParent(child, nullptr);
    LONG_PTR style = GetWindowLongPtrW(child, GWL_STYLE);
    style &= ~WS_CAPTION;
    style &= ~WS_THICKFRAME;
    style |= WS_POPUP | WS_VISIBLE;
    SetWindowLongPtrW(child, GWL_STYLE, style);

    LONG_PTR ex_style = GetWindowLongPtrW(child, GWL_EXSTYLE);
    ex_style &= ~WS_EX_APPWINDOW;
    ex_style |= WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE;
    SetWindowLongPtrW(child, GWL_EXSTYLE, ex_style);

    SetWindowPos(
        child,
        topmost ? HWND_TOPMOST : HWND_TOP,
        monitor_rect.left,
        monitor_rect.top,
        monitor_rect.right - monitor_rect.left,
        monitor_rect.bottom - monitor_rect.top,
        SWP_SHOWWINDOW | SWP_NOACTIVATE | SWP_FRAMECHANGED
    );
}

LRESULT CALLBACK WindowProc(HWND hwnd, UINT message, WPARAM wparam, LPARAM lparam) {
    switch (message) {
        case WM_PAINT: {
            PAINTSTRUCT ps{};
            HDC dc = BeginPaint(hwnd, &ps);
            RECT rect{};
            GetClientRect(hwnd, &rect);
            HBRUSH brush = CreateSolidBrush(RGB(0, 120, 255));
            FillRect(dc, &rect, brush);
            DeleteObject(brush);
            EndPaint(hwnd, &ps);
            return 0;
        }
        case WM_ERASEBKGND:
            return 1;
        case WM_NCHITTEST:
            return HTTRANSPARENT;
        case WM_MOUSEACTIVATE:
            return MA_NOACTIVATE;
        case WM_DESTROY:
            RestoreTransparentIconLayer();
            RestoreListViewStack();
            RestoreShellStack();
            PostQuitMessage(0);
            return 0;
        default:
            return DefWindowProcW(hwnd, message, wparam, lparam);
    }
}

HWND CreateBlueWindow(HINSTANCE instance, RECT monitor_rect) {
    WNDCLASSW wc{};
    wc.lpfnWndProc = WindowProc;
    wc.hInstance = instance;
    wc.lpszClassName = kWindowClass;
    wc.hbrBackground = nullptr;
    RegisterClassW(&wc);

    HWND hwnd = CreateWindowExW(
        WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE,
        kWindowClass,
        L"Movaura Native Host Probe",
        WS_POPUP | WS_VISIBLE,
        monitor_rect.left,
        monitor_rect.top,
        monitor_rect.right - monitor_rect.left,
        monitor_rect.bottom - monitor_rect.top,
        nullptr,
        nullptr,
        instance,
        nullptr
    );
    ShowWindow(hwnd, SW_SHOWNOACTIVATE);
    UpdateWindow(hwnd);
    return hwnd;
}

std::wstring ArgOrDefault(LPWSTR* argv, int argc, int index, const wchar_t* fallback) {
    if (index < argc && argv[index]) {
        return argv[index];
    }
    return fallback;
}

int RunWindowMode(HINSTANCE instance, const std::wstring& mode) {
    RECT monitor_rect = PrimaryMonitorRect();
    HWND hwnd = CreateBlueWindow(instance, monitor_rect);
    DesktopTopology topology = ProbeDesktop();
    PrintTopology(topology);
    PrintDirectChildren(L"Progman", topology.progman);
    PrintDirectChildren(L"SHELLDLL_DefView", topology.shell_defview);

    if (mode == L"workerw") {
        if (topology.workerw_after_defview) {
            AttachChild(hwnd, topology.workerw_after_defview, monitor_rect, false);
        } else {
            PrintLine(L"workerw mode failed: no WorkerW-after-DefView host.");
            DestroyWindow(hwnd);
            return 2;
        }
    } else if (mode == L"workerw-front") {
        if (topology.workerw_after_defview) {
            AttachChild(hwnd, topology.workerw_after_defview, monitor_rect, true);
        } else {
            PrintLine(L"workerw-front mode failed: no WorkerW-after-DefView host.");
            DestroyWindow(hwnd);
            return 2;
        }
    } else if (mode == L"workerw-shell-stack") {
        if (!AttachWorkerWShellStack(hwnd, topology, monitor_rect)) {
            DestroyWindow(hwnd);
            return 2;
        }
    } else if (mode == L"workerw-listview-stack") {
        if (!AttachWorkerWListViewStack(hwnd, topology, monitor_rect)) {
            DestroyWindow(hwnd);
            return 2;
        }
    } else if (mode == L"progman") {
        AttachChild(hwnd, topology.progman, monitor_rect, false);
    } else if (mode == L"progman-front") {
        AttachChild(hwnd, topology.progman, monitor_rect, true);
    } else if (mode == L"progman-stack") {
        if (!AttachProgmanStack(hwnd, topology, monitor_rect)) {
            DestroyWindow(hwnd);
            return 2;
        }
    } else if (mode == L"defview-under-icons") {
        if (topology.shell_defview && topology.sys_listview) {
            RECT parent_rect{};
            GetWindowRect(topology.shell_defview, &parent_rect);
            PrepareChild(hwnd);
            SetParent(hwnd, topology.shell_defview);
            SetWindowPos(
                hwnd,
                topology.sys_listview,
                monitor_rect.left - parent_rect.left,
                monitor_rect.top - parent_rect.top,
                monitor_rect.right - monitor_rect.left,
                monitor_rect.bottom - monitor_rect.top,
                SWP_SHOWWINDOW | SWP_NOACTIVATE | SWP_FRAMECHANGED
            );
        } else {
            PrintLine(L"defview-under-icons mode failed: missing DefView/ListView.");
            DestroyWindow(hwnd);
            return 2;
        }
    } else if (mode == L"defview-transparent-icons") {
        if (!AttachDefViewTransparentIcons(hwnd, topology, monitor_rect)) {
            DestroyWindow(hwnd);
            return 2;
        }
    } else if (mode == L"listview") {
        AttachChild(hwnd, topology.sys_listview, monitor_rect, false);
    } else if (mode == L"desktop-overlay") {
        AttachTopLevel(hwnd, monitor_rect, false);
    } else if (mode == L"overlay") {
        AttachTopLevel(hwnd, monitor_rect, true);
    } else {
        PrintLine(L"Unknown mode: " + mode);
        DestroyWindow(hwnd);
        return 2;
    }

    PrintLine(L"Native host app mode active: " + mode);
    MSG msg{};
    while (GetMessageW(&msg, nullptr, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }
    return 0;
}

}  // namespace

int wmain(int argc, wchar_t** argv) {
    HINSTANCE instance = GetModuleHandleW(nullptr);
    std::wstring mode = ArgOrDefault(argv, argc, 1, L"probe");

    if (mode == L"probe") {
        DesktopTopology topology = ProbeDesktop();
        PrintTopology(topology);
        return 0;
    }

    int result = RunWindowMode(instance, mode);
    return result;
}
