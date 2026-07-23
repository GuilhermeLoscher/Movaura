// Movaura native compositor. Desenvolvido por Guilherme Loscher (GL).
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <shellapi.h>
#include <mmsystem.h>

#include <d2d1.h>
#include <d3d10.h>
#include <d3d11.h>
#include <dcomp.h>
#include <dxgi1_2.h>
#include <mfapi.h>
#include <mfidl.h>
#include <mfreadwrite.h>
#include <mmdeviceapi.h>
#include <endpointvolume.h>
#include <wincodec.h>
#include <wrl/client.h>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <condition_variable>
#include <cwchar>
#include <cwctype>
#include <cstring>
#include <deque>
#include <iomanip>
#include <iostream>
#include <mutex>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

using Microsoft::WRL::ComPtr;

namespace {

constexpr wchar_t kWindowClass[] = L"MovauraNativeCompositorPreview";
constexpr wchar_t kWindowTitle[] = L"Movaura Native Composition Preview";
constexpr wchar_t kSingleInstanceMutexPrefix[] = L"Local\\MovauraNativeCompositorPreview_";
constexpr UINT_PTR kAnimationTimer = 1;
constexpr UINT kSpawnWorkerW = 0x052C;
constexpr LONG_PTR kWsExNoRedirectionBitmap = 0x00200000L;
constexpr size_t kVideoQueueCapacity = 2;
constexpr size_t kVideoRecycleCapacity = 1;
constexpr UINT kMaxVideoDecodeWidth = 1920;
constexpr UINT kMaxVideoDecodeHeight = 1080;
constexpr UINT kMaxCompositorFps = 60;
constexpr UINT kMinAnimationTimerMs = 15;

struct PreviewOptions {
    UINT fps = 30;
    UINT effect_intensity = 70;
    UINT effect_speed = 100;
    D2D1_COLOR_F color = D2D1::ColorF(0.0f, 120.0f / 255.0f, 1.0f, 1.0f);
    std::wstring scene = L"pulse";
    std::wstring file;
    std::wstring instance_key = L"preview";
    int x = CW_USEDEFAULT;
    int y = CW_USEDEFAULT;
    int width = 960;
    int height = 540;
    bool fullscreen = false;
    bool desktop_experimental = false;
    bool desktop_live = false;
    bool replace_existing = false;
    bool prefer_low_cpu = false;
    UINT video_max_width = kMaxVideoDecodeWidth;
    UINT video_max_height = kMaxVideoDecodeHeight;
    std::vector<RECT> repeat_monitors;
};

PreviewOptions g_options;
HWND g_desktop_progman = nullptr;
HWND g_desktop_shell_defview = nullptr;
HWND g_desktop_workerw = nullptr;

bool IsAnimatedScene() {
    return g_options.scene == L"video"
        || g_options.scene == L"gif"
        || g_options.scene == L"pulse"
        || g_options.scene == L"audio"
        || g_options.scene == L"parallax"
        || g_options.scene == L"particles"
        || g_options.scene == L"rain"
        || g_options.scene == L"fog"
        || g_options.scene == L"glow"
        || g_options.scene == L"vignette";
}

UINT RenderTimerIntervalMs() {
    if (!IsAnimatedScene()) {
        return 1000U;
    }
    return std::max(kMinAnimationTimerMs, 1000U / std::max(1U, std::min(g_options.fps, kMaxCompositorFps)));
}

std::wstring WindowTitle() {
    return std::wstring(kWindowTitle) + L" [" + g_options.instance_key + L"]";
}

std::wstring SingleInstanceMutex() {
    return std::wstring(kSingleInstanceMutexPrefix) + g_options.instance_key;
}

std::wstring HResultText(HRESULT hr) {
    std::wstringstream stream;
    stream << L"0x" << std::hex << std::setw(8) << std::setfill(L'0')
           << static_cast<unsigned long>(hr);
    return stream.str();
}

HWND FindProgman() {
    HWND progman = FindWindowW(L"Progman", L"Program Manager");
    return progman ? progman : FindWindowW(L"Progman", nullptr);
}

bool AttachToProgmanStack(HWND hwnd, int x, int y, int width, int height) {
    HWND progman = FindProgman();
    HWND shell_defview = progman
        ? FindWindowExW(progman, nullptr, L"SHELLDLL_DefView", nullptr)
        : nullptr;
    if (!progman || !shell_defview) {
        return false;
    }

    RECT progman_rect{};
    if (!GetWindowRect(progman, &progman_rect)) {
        return false;
    }

    LONG_PTR style = GetWindowLongPtrW(hwnd, GWL_STYLE);
    style &= ~(WS_POPUP | WS_CAPTION | WS_THICKFRAME);
    style |= WS_CHILD;
    SetWindowLongPtrW(hwnd, GWL_STYLE, style);

    LONG_PTR ex_style = GetWindowLongPtrW(hwnd, GWL_EXSTYLE);
    ex_style &= ~WS_EX_APPWINDOW;
    ex_style |= WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE | WS_EX_TRANSPARENT;
    SetWindowLongPtrW(hwnd, GWL_EXSTYLE, ex_style);

    SetLastError(ERROR_SUCCESS);
    SetParent(hwnd, progman);
    if (GetParent(hwnd) != progman) {
        return false;
    }

    int child_x = x - progman_rect.left;
    int child_y = y - progman_rect.top;
    BOOL wallpaper_positioned = SetWindowPos(
        hwnd,
        HWND_BOTTOM,
        child_x,
        child_y,
        width,
        height,
        SWP_NOACTIVATE | SWP_FRAMECHANGED
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
    return wallpaper_positioned != FALSE && icons_positioned != FALSE;
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
            GetClassNameW(child, child_class, ARRAYSIZE(child_class));
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

HWND FindWorkerWAfterDefView(HWND progman, HWND shell_defview) {
    if (!progman || !shell_defview || GetParent(shell_defview) != progman) {
        return nullptr;
    }
    return FindWindowExW(progman, shell_defview, L"WorkerW", nullptr);
}

HWND FindClassicWallpaperWorkerW() {
    struct WorkerContext {
        HWND workerw;
    } context{nullptr};
    EnumWindows(
        [](HWND top_level, LPARAM lparam) -> BOOL {
            auto* context = reinterpret_cast<WorkerContext*>(lparam);
            HWND shell_defview = FindWindowExW(
                top_level,
                nullptr,
                L"SHELLDLL_DefView",
                nullptr
            );
            if (!shell_defview) {
                return TRUE;
            }
            context->workerw = FindWindowExW(
                nullptr,
                top_level,
                L"WorkerW",
                nullptr
            );
            return context->workerw ? FALSE : TRUE;
        },
        reinterpret_cast<LPARAM>(&context)
    );
    return context.workerw;
}

bool AttachToRaisedDesktop(HWND hwnd, int x, int y, int width, int height) {
    HWND progman = FindProgman();
    if (!progman) {
        return false;
    }

    LONG_PTR progman_ex_style = GetWindowLongPtrW(progman, GWL_EXSTYLE);
    if ((progman_ex_style & kWsExNoRedirectionBitmap) == 0) {
        return false;
    }

    DWORD_PTR message_result = 0;
    SendMessageTimeoutW(
        progman,
        kSpawnWorkerW,
        static_cast<WPARAM>(0xD),
        static_cast<LPARAM>(0x1),
        SMTO_NORMAL,
        1000,
        &message_result
    );

    HWND shell_defview = FindChildDeep(progman, L"SHELLDLL_DefView");
    HWND workerw = FindWorkerWAfterDefView(progman, shell_defview);
    if (!shell_defview || !workerw) {
        return false;
    }

    RECT progman_rect{};
    if (!GetWindowRect(progman, &progman_rect)) {
        return false;
    }

    LONG_PTR style = GetWindowLongPtrW(hwnd, GWL_STYLE);
    style &= ~(WS_POPUP | WS_CAPTION | WS_THICKFRAME);
    style |= WS_CHILD;
    SetWindowLongPtrW(hwnd, GWL_STYLE, style);

    LONG_PTR ex_style = GetWindowLongPtrW(hwnd, GWL_EXSTYLE);
    ex_style &= ~(WS_EX_APPWINDOW | WS_EX_TRANSPARENT | WS_EX_LAYERED);
    ex_style |= WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE;
    SetWindowLongPtrW(hwnd, GWL_EXSTYLE, ex_style);

    SetParent(hwnd, progman);
    if (GetParent(hwnd) != progman) {
        return false;
    }

    BOOL wallpaper_positioned = SetWindowPos(
        hwnd,
        shell_defview,
        x - progman_rect.left,
        y - progman_rect.top,
        width,
        height,
        SWP_NOACTIVATE | SWP_FRAMECHANGED
    );
    BOOL workerw_positioned = SetWindowPos(
        workerw,
        HWND_BOTTOM,
        0,
        0,
        0,
        0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
    );
    if (wallpaper_positioned != FALSE && workerw_positioned != FALSE) {
        g_desktop_progman = progman;
        g_desktop_shell_defview = shell_defview;
        g_desktop_workerw = workerw;
    }
    return wallpaper_positioned != FALSE && workerw_positioned != FALSE;
}

bool AttachToClassicDesktop(HWND hwnd, int x, int y, int width, int height) {
    HWND progman = FindProgman();
    if (!progman) {
        return false;
    }

    DWORD_PTR message_result = 0;
    SendMessageTimeoutW(
        progman,
        kSpawnWorkerW,
        static_cast<WPARAM>(0xD),
        static_cast<LPARAM>(0x1),
        SMTO_NORMAL,
        1000,
        &message_result
    );

    HWND workerw = FindClassicWallpaperWorkerW();
    RECT workerw_rect{};
    if (!workerw || !GetWindowRect(workerw, &workerw_rect)) {
        return false;
    }

    LONG_PTR style = GetWindowLongPtrW(hwnd, GWL_STYLE);
    style &= ~(WS_POPUP | WS_CAPTION | WS_THICKFRAME);
    style |= WS_CHILD;
    SetWindowLongPtrW(hwnd, GWL_STYLE, style);

    LONG_PTR ex_style = GetWindowLongPtrW(hwnd, GWL_EXSTYLE);
    ex_style &= ~WS_EX_APPWINDOW;
    ex_style |= WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE;
    SetWindowLongPtrW(hwnd, GWL_EXSTYLE, ex_style);

    SetParent(hwnd, workerw);
    if (GetParent(hwnd) != workerw) {
        return false;
    }

    BOOL positioned = SetWindowPos(
        hwnd,
        HWND_BOTTOM,
        x - workerw_rect.left,
        y - workerw_rect.top,
        width,
        height,
        SWP_NOACTIVATE | SWP_FRAMECHANGED
    );
    if (positioned != FALSE) {
        g_desktop_progman = nullptr;
        g_desktop_shell_defview = nullptr;
        g_desktop_workerw = workerw;
    }
    return positioned != FALSE;
}

bool AttachToDesktop(HWND hwnd, int x, int y, int width, int height) {
    return AttachToRaisedDesktop(hwnd, x, y, width, height)
        || AttachToClassicDesktop(hwnd, x, y, width, height);
}

bool IsDesktopHostValid(HWND hwnd) {
    if (!IsWindow(hwnd) || !IsWindow(g_desktop_workerw)) {
        return false;
    }
    if (!g_desktop_progman) {
        return GetParent(hwnd) == g_desktop_workerw;
    }
    return IsWindow(g_desktop_progman)
        && IsWindow(g_desktop_shell_defview)
        && GetParent(hwnd) == g_desktop_progman
        && GetParent(g_desktop_shell_defview) == g_desktop_progman
        && GetParent(g_desktop_workerw) == g_desktop_progman;
}

void PrintFailure(const wchar_t* operation, HRESULT hr) {
    std::wcerr << L"[error] " << operation << L" failed: " << HResultText(hr) << std::endl;
}

D2D1_RECT_F CoverSourceRect(float source_width, float source_height, float target_width, float target_height) {
    if (source_width <= 0.0f || source_height <= 0.0f || target_width <= 0.0f || target_height <= 0.0f) {
        return D2D1::RectF(0.0f, 0.0f, source_width, source_height);
    }
    const float source_aspect = source_width / source_height;
    const float target_aspect = target_width / target_height;
    if (source_aspect > target_aspect) {
        const float visible_width = source_height * target_aspect;
        const float left = (source_width - visible_width) * 0.5f;
        return D2D1::RectF(left, 0.0f, left + visible_width, source_height);
    }
    const float visible_height = source_width / target_aspect;
    const float top = (source_height - visible_height) * 0.5f;
    return D2D1::RectF(0.0f, top, source_width, top + visible_height);
}

D2D1_RECT_F ParallaxDestinationRect(D2D1_RECT_F destination) {
    if (g_options.scene != L"parallax") {
        return destination;
    }
    POINT cursor{};
    if (!GetCursorPos(&cursor)) {
        return destination;
    }
    const float width = destination.right - destination.left;
    const float height = destination.bottom - destination.top;
    if (width <= 0.0f || height <= 0.0f) {
        return destination;
    }
    const float normalized_x = std::clamp(
        (static_cast<float>(cursor.x) - destination.left) / width,
        0.0f,
        1.0f
    );
    const float normalized_y = std::clamp(
        (static_cast<float>(cursor.y) - destination.top) / height,
        0.0f,
        1.0f
    );
    const float centered_x = (normalized_x - 0.5f) * 2.0f;
    const float centered_y = (normalized_y - 0.5f) * 2.0f;
    const float intensity = std::clamp(g_options.effect_intensity / 100.0f, 0.0f, 1.0f);
    const float overscan = 0.025f + intensity * 0.035f;
    const float extra_x = width * overscan;
    const float extra_y = height * overscan;
    const float shift_x = centered_x * extra_x * 0.5f;
    const float shift_y = centered_y * extra_y * 0.5f;
    return D2D1::RectF(
        destination.left - extra_x + shift_x,
        destination.top - extra_y + shift_y,
        destination.right + extra_x + shift_x,
        destination.bottom + extra_y + shift_y
    );
}

void DrawBitmapCovered(
    ID2D1RenderTarget* render_target,
    ID2D1Bitmap* bitmap,
    const D2D1_SIZE_F& bitmap_size,
    const D2D1_SIZE_F& target_size
) {
    if (g_options.repeat_monitors.empty()) {
        const D2D1_RECT_F target = D2D1::RectF(0.0f, 0.0f, target_size.width, target_size.height);
        render_target->PushAxisAlignedClip(target, D2D1_ANTIALIAS_MODE_ALIASED);
        render_target->DrawBitmap(
            bitmap,
            ParallaxDestinationRect(target),
            1.0f,
            D2D1_BITMAP_INTERPOLATION_MODE_LINEAR,
            CoverSourceRect(bitmap_size.width, bitmap_size.height, target_size.width, target_size.height)
        );
        render_target->PopAxisAlignedClip();
        return;
    }
    for (const RECT& monitor : g_options.repeat_monitors) {
        const float width = static_cast<float>(monitor.right - monitor.left);
        const float height = static_cast<float>(monitor.bottom - monitor.top);
        const D2D1_RECT_F target = D2D1::RectF(
            static_cast<float>(monitor.left),
            static_cast<float>(monitor.top),
            static_cast<float>(monitor.right),
            static_cast<float>(monitor.bottom)
        );
        render_target->PushAxisAlignedClip(target, D2D1_ANTIALIAS_MODE_ALIASED);
        render_target->DrawBitmap(
            bitmap,
            ParallaxDestinationRect(target),
            1.0f,
            D2D1_BITMAP_INTERPOLATION_MODE_LINEAR,
            CoverSourceRect(bitmap_size.width, bitmap_size.height, width, height)
        );
        render_target->PopAxisAlignedClip();
    }
}

class NativeCompositor {
public:
    ~NativeCompositor() {
        StopVideoDecoder();
        if (media_foundation_started_) {
            MFShutdown();
        }
    }

    bool IsInitialized() const {
        return dcomp_device_ && visual_;
    }

    HRESULT Initialize(HWND hwnd, UINT width, UINT height) {
        hwnd_ = hwnd;

        HRESULT hr = D2D1CreateFactory(
            D2D1_FACTORY_TYPE_SINGLE_THREADED,
            d2d_factory_.ReleaseAndGetAddressOf()
        );
        if (FAILED(hr)) {
            return hr;
        }

        hr = InitializeGraphicsResources();
        if (FAILED(hr)) {
            return hr;
        }

        if (g_options.scene == L"image") {
            hr = InitializeImage();
            if (FAILED(hr)) {
                return hr;
            }
        } else if (g_options.scene == L"gif") {
            hr = InitializeGif();
            if (FAILED(hr)) {
                return hr;
            }
        } else if (g_options.scene == L"video") {
            hr = InitializeVideo();
            if (FAILED(hr)) {
                PrintFailure(L"InitializeVideo", hr);
                return hr;
            }
        } else if (
            g_options.scene == L"audio" || g_options.scene == L"parallax"
            || g_options.scene == L"particles" || g_options.scene == L"rain"
            || g_options.scene == L"fog" || g_options.scene == L"glow"
            || g_options.scene == L"vignette"
        ) {
            if (g_options.scene == L"audio") {
                InitializeAudioMeter();
            }
            hr = InitializeLayeredBackground();
            if (FAILED(hr)) {
                return hr;
            }
        }

        hr = Render(width, height);
        if (FAILED(hr) && g_options.scene == L"video" && !disable_dxgi_video_) {
            PrintFailure(L"Render hardware video path", hr);
            StopVideoDecoder();
            ResetVideoPlaybackState();
            disable_dxgi_video_ = true;
            hr = InitializeVideo();
            if (SUCCEEDED(hr)) {
                hr = Render(width, height);
            }
        }
        return hr;
    }

    HRESULT InitializeGraphicsResources() {
        HRESULT hr = S_OK;
        D3D_FEATURE_LEVEL feature_level{};
        UINT device_flags = D3D11_CREATE_DEVICE_BGRA_SUPPORT | D3D11_CREATE_DEVICE_VIDEO_SUPPORT;
        hr = D3D11CreateDevice(
            nullptr,
            D3D_DRIVER_TYPE_HARDWARE,
            nullptr,
            device_flags,
            nullptr,
            0,
            D3D11_SDK_VERSION,
            d3d_device_.ReleaseAndGetAddressOf(),
            &feature_level,
            nullptr
        );
        if (FAILED(hr)) {
            device_flags = D3D11_CREATE_DEVICE_BGRA_SUPPORT;
            hr = D3D11CreateDevice(
                nullptr,
                D3D_DRIVER_TYPE_HARDWARE,
                nullptr,
                device_flags,
                nullptr,
                0,
                D3D11_SDK_VERSION,
                d3d_device_.ReleaseAndGetAddressOf(),
                &feature_level,
                nullptr
            );
        }
        if (FAILED(hr)) {
            hr = D3D11CreateDevice(
                nullptr,
                D3D_DRIVER_TYPE_WARP,
                nullptr,
                D3D11_CREATE_DEVICE_BGRA_SUPPORT,
                nullptr,
                0,
                D3D11_SDK_VERSION,
                d3d_device_.ReleaseAndGetAddressOf(),
                &feature_level,
                nullptr
            );
        }
        if (FAILED(hr)) {
            return hr;
        }

        ComPtr<ID3D10Multithread> multithread;
        if (SUCCEEDED(d3d_device_.As(&multithread))) {
            multithread->SetMultithreadProtected(TRUE);
        }

        ComPtr<IDXGIDevice> dxgi_device;
        hr = d3d_device_.As(&dxgi_device);
        if (FAILED(hr)) {
            return hr;
        }

        hr = DCompositionCreateDevice(
            dxgi_device.Get(),
            __uuidof(IDCompositionDevice),
            reinterpret_cast<void**>(dcomp_device_.ReleaseAndGetAddressOf())
        );
        if (FAILED(hr)) {
            return hr;
        }

        hr = dcomp_device_->CreateTargetForHwnd(hwnd_, TRUE, target_.ReleaseAndGetAddressOf());
        if (FAILED(hr)) {
            return hr;
        }

        hr = dcomp_device_->CreateVisual(visual_.ReleaseAndGetAddressOf());
        if (FAILED(hr)) {
            return hr;
        }

        hr = target_->SetRoot(visual_.Get());
        if (FAILED(hr)) {
            return hr;
        }

        return S_OK;
    }

    HRESULT Render(UINT width, UINT height) {
        if (!dcomp_device_ || !visual_ || width == 0 || height == 0) {
            return E_INVALIDARG;
        }

        HRESULT hr = S_OK;
        bool surface_changed = false;
        if (!surface_ || width != surface_width_ || height != surface_height_) {
            surface_.Reset();
            hr = dcomp_device_->CreateSurface(
                width,
                height,
                DXGI_FORMAT_B8G8R8A8_UNORM,
                DXGI_ALPHA_MODE_IGNORE,
                surface_.ReleaseAndGetAddressOf()
            );
            if (FAILED(hr)) {
                PrintFailure(L"CreateSurface", hr);
                return hr;
            }
            surface_width_ = width;
            surface_height_ = height;
            surface_changed = true;

            hr = visual_->SetContent(surface_.Get());
            if (FAILED(hr)) {
                PrintFailure(L"SetContent", hr);
                return hr;
            }
        }

        bool content_changed = surface_changed || !rendered_once_;
        if (
            g_options.scene == L"video"
            || ((g_options.scene == L"audio" || g_options.scene == L"parallax" || g_options.scene == L"particles" || g_options.scene == L"rain" || g_options.scene == L"fog" || g_options.scene == L"glow" || g_options.scene == L"vignette") && video_reader_)
        ) {
            content_changed = AdvanceVideoFrame() || content_changed;
        } else if (
            (g_options.scene == L"gif" || g_options.scene == L"audio" || g_options.scene == L"parallax" || g_options.scene == L"particles" || g_options.scene == L"rain" || g_options.scene == L"fog" || g_options.scene == L"glow" || g_options.scene == L"vignette")
            && !gif_frames_.empty()
        ) {
            content_changed = AdvanceGifFrame() || content_changed;
        } else if (
            g_options.scene == L"pulse"
            || g_options.scene == L"parallax"
            || g_options.scene == L"audio"
            || g_options.scene == L"particles"
            || g_options.scene == L"rain"
            || g_options.scene == L"fog"
            || g_options.scene == L"glow"
            || g_options.scene == L"vignette"
        ) {
            content_changed = true;
        }
        if (!content_changed) {
            return S_OK;
        }

        POINT offset{};
        ComPtr<IDXGISurface> dxgi_surface;
        hr = surface_->BeginDraw(
            nullptr,
            __uuidof(IDXGISurface),
            reinterpret_cast<void**>(dxgi_surface.ReleaseAndGetAddressOf()),
            &offset
        );
        if (FAILED(hr)) {
            PrintFailure(L"BeginDraw", hr);
            return hr;
        }

        D2D1_RENDER_TARGET_PROPERTIES properties = D2D1::RenderTargetProperties(
            D2D1_RENDER_TARGET_TYPE_DEFAULT,
            D2D1::PixelFormat(DXGI_FORMAT_B8G8R8A8_UNORM, D2D1_ALPHA_MODE_IGNORE)
        );
        ComPtr<ID2D1RenderTarget> render_target;
        hr = d2d_factory_->CreateDxgiSurfaceRenderTarget(
            dxgi_surface.Get(),
            &properties,
            render_target.ReleaseAndGetAddressOf()
        );
        if (FAILED(hr)) {
            PrintFailure(L"CreateDxgiSurfaceRenderTarget", hr);
        }
        if (SUCCEEDED(hr)) {
            render_target->BeginDraw();
            render_target->Clear(g_options.color);

            D2D1_SIZE_F size = render_target->GetSize();
            IWICFormatConverter* frame_converter = nullptr;
            if (
                g_options.scene == L"image"
                || ((g_options.scene == L"audio" || g_options.scene == L"parallax" || g_options.scene == L"particles" || g_options.scene == L"rain" || g_options.scene == L"fog" || g_options.scene == L"glow" || g_options.scene == L"vignette") && image_converter_)
            ) {
                frame_converter = image_converter_.Get();
            } else if (
                (g_options.scene == L"gif" || g_options.scene == L"audio" || g_options.scene == L"parallax" || g_options.scene == L"particles" || g_options.scene == L"rain" || g_options.scene == L"fog" || g_options.scene == L"glow" || g_options.scene == L"vignette")
                && !gif_frames_.empty()
            ) {
                frame_converter = gif_frames_[gif_frame_index_].Get();
            }

            if (frame_converter) {
                ComPtr<ID2D1Bitmap> bitmap;
                hr = render_target->CreateBitmapFromWicBitmap(
                    frame_converter,
                    bitmap.ReleaseAndGetAddressOf()
                );
                if (SUCCEEDED(hr)) {
                    const D2D1_SIZE_F bitmap_size = bitmap->GetSize();
                    DrawBitmapCovered(render_target.Get(), bitmap.Get(), bitmap_size, size);
                }
            } else if (
                (g_options.scene == L"video" || g_options.scene == L"audio" || g_options.scene == L"parallax" || g_options.scene == L"particles" || g_options.scene == L"rain" || g_options.scene == L"fog" || g_options.scene == L"glow" || g_options.scene == L"vignette")
                && !video_current_frame_.pixels.empty()
            ) {
                ComPtr<ID2D1Bitmap> bitmap;
                hr = render_target->CreateBitmap(
                    D2D1::SizeU(video_width_, video_height_),
                    video_current_frame_.pixels.data(),
                    video_width_ * 4,
                    D2D1::BitmapProperties(
                        D2D1::PixelFormat(
                            DXGI_FORMAT_B8G8R8A8_UNORM,
                            D2D1_ALPHA_MODE_IGNORE
                        )
                    ),
                    bitmap.ReleaseAndGetAddressOf()
                );
                if (SUCCEEDED(hr)) {
                    DrawBitmapCovered(
                        render_target.Get(),
                        bitmap.Get(),
                        D2D1::SizeF(
                            static_cast<float>(video_width_),
                            static_cast<float>(video_height_)
                        ),
                        size
                    );
                } else if (g_options.scene == L"video") {
                    hr = S_OK;
                }
            }
            if (g_options.scene == L"pulse") {
                ComPtr<ID2D1SolidColorBrush> brush;
                hr = render_target->CreateSolidColorBrush(
                    D2D1::ColorF(1.0f, 1.0f, 1.0f, 0.04f + g_options.effect_intensity * 0.0026f),
                    brush.ReleaseAndGetAddressOf()
                );
                double seconds = std::chrono::duration<double>(
                    std::chrono::steady_clock::now().time_since_epoch()
                ).count();
                const float speed = g_options.effect_speed / 100.0f;
                float pulse = static_cast<float>((std::sin(seconds * 1.4 * speed) + 1.0) * 0.5);
                float travel = static_cast<float>((std::sin(seconds * 0.7 * speed) + 1.0) * 0.5);
                float band_top = size.height * (0.08f + travel * 0.68f);
                float band_height = size.height * (0.045f + pulse * 0.035f);
                if (SUCCEEDED(hr)) {
                    render_target->FillRectangle(
                        D2D1::RectF(size.width * 0.08f, band_top, size.width * 0.92f, band_top + band_height),
                        brush.Get()
                    );
                }
            }
            if (g_options.scene == L"audio") {
                ComPtr<ID2D1SolidColorBrush> brush;
                hr = render_target->CreateSolidColorBrush(
                    D2D1::ColorF(1.0f, 1.0f, 1.0f, 0.12f + g_options.effect_intensity * 0.008f),
                    brush.ReleaseAndGetAddressOf()
                );
                float peak = AudioPeak();
                const int bars = 24;
                const float gap = size.width * 0.008f;
                const float bar_width = (size.width - gap * (bars + 1)) / bars;
                double seconds = std::chrono::duration<double>(
                    std::chrono::steady_clock::now().time_since_epoch()
                ).count();
                if (SUCCEEDED(hr)) {
                    for (int index = 0; index < bars; ++index) {
                        float wave = static_cast<float>((std::sin(seconds * 4.0 * g_options.effect_speed / 100.0 + index * 0.72) + 1.0) * 0.5);
                        float intensity = g_options.effect_intensity / 100.0f;
                        float bar_height = size.height * (0.04f + peak * intensity * (0.18f + wave * 0.72f));
                        float left = gap + index * (bar_width + gap);
                        render_target->FillRectangle(
                            D2D1::RectF(left, size.height - bar_height, left + bar_width, size.height),
                            brush.Get()
                        );
                    }
                }
            }
            if (
                g_options.scene == L"particles" || g_options.scene == L"rain"
                || g_options.scene == L"fog" || g_options.scene == L"glow"
                || g_options.scene == L"vignette"
            ) {
                ComPtr<ID2D1SolidColorBrush> brush;
                const float intensity = g_options.effect_intensity / 100.0f;
                hr = render_target->CreateSolidColorBrush(
                    D2D1::ColorF(1.0f, 1.0f, 1.0f, 0.04f + intensity * 0.20f),
                    brush.ReleaseAndGetAddressOf()
                );
                const double seconds = std::chrono::duration<double>(
                    std::chrono::steady_clock::now().time_since_epoch()
                ).count() * g_options.effect_speed / 100.0;
                if (SUCCEEDED(hr) && g_options.scene == L"rain") {
                    for (int index = 0; index < 42; ++index) {
                        const float x = std::fmod(index * 97.0f + static_cast<float>(seconds * 180.0), size.width + 80.0f) - 40.0f;
                        const float y = std::fmod(index * 61.0f + static_cast<float>(seconds * 290.0), size.height + 120.0f) - 60.0f;
                        render_target->DrawLine(D2D1::Point2F(x, y), D2D1::Point2F(x - 12.0f, y + 34.0f), brush.Get(), 1.4f);
                    }
                } else if (SUCCEEDED(hr) && g_options.scene == L"particles") {
                    for (int index = 0; index < 34; ++index) {
                        const float x = std::fmod(index * 113.0f + static_cast<float>(seconds * 32.0), size.width);
                        const float y = std::fmod(index * 71.0f + static_cast<float>(seconds * 18.0), size.height);
                        render_target->FillEllipse(D2D1::Ellipse(D2D1::Point2F(x, y), 1.5f + intensity * 3.0f, 1.5f + intensity * 3.0f), brush.Get());
                    }
                } else if (SUCCEEDED(hr) && (g_options.scene == L"fog" || g_options.scene == L"glow")) {
                    const float wave = static_cast<float>((std::sin(seconds * 0.8) + 1.0) * 0.5);
                    const float margin = size.width * (0.08f + wave * 0.08f);
                    render_target->FillRectangle(D2D1::RectF(margin, size.height * 0.25f, size.width - margin, size.height * 0.75f), brush.Get());
                } else if (SUCCEEDED(hr)) {
                    const float margin_x = size.width * (0.04f + intensity * 0.12f);
                    const float margin_y = size.height * (0.04f + intensity * 0.12f);
                    render_target->DrawRectangle(D2D1::RectF(margin_x, margin_y, size.width - margin_x, size.height - margin_y), brush.Get(), 10.0f + intensity * 36.0f);
                }
            }
            HRESULT draw_hr = render_target->EndDraw();
            if (SUCCEEDED(hr)) {
                hr = draw_hr;
            }
        }

        HRESULT end_draw_hr = surface_->EndDraw();
        if (FAILED(hr)) {
            PrintFailure(L"Render body", hr);
            return hr;
        }
        if (FAILED(end_draw_hr)) {
            PrintFailure(L"EndDraw", end_draw_hr);
            return end_draw_hr;
        }

        hr = dcomp_device_->Commit();
        if (FAILED(hr)) {
            PrintFailure(L"Commit", hr);
        }
        if (SUCCEEDED(hr)) {
            rendered_once_ = true;
        }
        return hr;
    }

private:
    HRESULT InitializeLayeredBackground() {
        if (g_options.file.empty()) {
            return S_OK;
        }
        std::wstring extension;
        const size_t dot = g_options.file.find_last_of(L'.');
        if (dot != std::wstring::npos) {
            extension = g_options.file.substr(dot);
            std::transform(extension.begin(), extension.end(), extension.begin(), towlower);
        }
        if (
            extension == L".bmp"
            || extension == L".jpeg"
            || extension == L".jpg"
            || extension == L".png"
            || extension == L".webp"
        ) {
            return InitializeImage();
        }
        if (extension == L".gif") {
            return InitializeGif();
        }
        if (extension == L".mp4" || extension == L".webm") {
            return InitializeVideo();
        }
        return S_OK;
    }

    void InitializeAudioMeter() {
        ComPtr<IMMDevice> device;
        if (FAILED(CoCreateInstance(
            __uuidof(MMDeviceEnumerator),
            nullptr,
            CLSCTX_INPROC_SERVER,
            IID_PPV_ARGS(audio_enumerator_.ReleaseAndGetAddressOf())
        ))) {
            return;
        }
        if (FAILED(audio_enumerator_->GetDefaultAudioEndpoint(
            eRender,
            eConsole,
            device.ReleaseAndGetAddressOf()
        ))) {
            return;
        }
        device->Activate(
            __uuidof(IAudioMeterInformation),
            CLSCTX_INPROC_SERVER,
            nullptr,
            reinterpret_cast<void**>(audio_meter_.ReleaseAndGetAddressOf())
        );
    }

    float AudioPeak() {
        float peak = 0.0f;
        if (audio_meter_) {
            audio_meter_->GetPeakValue(&peak);
        }
        return std::clamp(peak, 0.0f, 1.0f);
    }

    HRESULT InitializeImage() {
        if (g_options.file.empty()) {
            return E_INVALIDARG;
        }

        HRESULT hr = EnsureWicFactory();
        if (FAILED(hr)) {
            return hr;
        }

        ComPtr<IWICBitmapDecoder> decoder;
        hr = wic_factory_->CreateDecoderFromFilename(
            g_options.file.c_str(),
            nullptr,
            GENERIC_READ,
            WICDecodeMetadataCacheOnLoad,
            decoder.ReleaseAndGetAddressOf()
        );
        if (FAILED(hr)) {
            return hr;
        }

        ComPtr<IWICBitmapFrameDecode> frame;
        hr = decoder->GetFrame(0, frame.ReleaseAndGetAddressOf());
        if (FAILED(hr)) {
            return hr;
        }

        hr = wic_factory_->CreateFormatConverter(image_converter_.ReleaseAndGetAddressOf());
        if (FAILED(hr)) {
            return hr;
        }

        return image_converter_->Initialize(
            frame.Get(),
            GUID_WICPixelFormat32bppPBGRA,
            WICBitmapDitherTypeNone,
            nullptr,
            0.0,
            WICBitmapPaletteTypeMedianCut
        );
    }

    HRESULT InitializeGif() {
        if (g_options.file.empty()) {
            return E_INVALIDARG;
        }

        HRESULT hr = EnsureWicFactory();
        if (FAILED(hr)) {
            return hr;
        }

        ComPtr<IWICBitmapDecoder> decoder;
        hr = wic_factory_->CreateDecoderFromFilename(
            g_options.file.c_str(),
            nullptr,
            GENERIC_READ,
            WICDecodeMetadataCacheOnLoad,
            decoder.ReleaseAndGetAddressOf()
        );
        if (FAILED(hr)) {
            return hr;
        }

        UINT frame_count = 0;
        hr = decoder->GetFrameCount(&frame_count);
        if (FAILED(hr) || frame_count == 0) {
            return FAILED(hr) ? hr : E_FAIL;
        }

        gif_frames_.reserve(frame_count);
        gif_frame_delays_ms_.reserve(frame_count);
        for (UINT index = 0; index < frame_count; ++index) {
            ComPtr<IWICBitmapFrameDecode> frame;
            hr = decoder->GetFrame(index, frame.ReleaseAndGetAddressOf());
            if (FAILED(hr)) {
                return hr;
            }

            ComPtr<IWICFormatConverter> converter;
            hr = wic_factory_->CreateFormatConverter(converter.ReleaseAndGetAddressOf());
            if (FAILED(hr)) {
                return hr;
            }
            hr = converter->Initialize(
                frame.Get(),
                GUID_WICPixelFormat32bppPBGRA,
                WICBitmapDitherTypeNone,
                nullptr,
                0.0,
                WICBitmapPaletteTypeMedianCut
            );
            if (FAILED(hr)) {
                return hr;
            }

            gif_frames_.push_back(converter);
            gif_frame_delays_ms_.push_back(ReadGifFrameDelayMs(frame.Get()));
        }

        gif_frame_index_ = 0;
        gif_next_frame_at_ = std::chrono::steady_clock::now()
            + std::chrono::milliseconds(gif_frame_delays_ms_[0]);
        return S_OK;
    }

    HRESULT EnsureWicFactory() {
        if (wic_factory_) {
            return S_OK;
        }
        return CoCreateInstance(
            CLSID_WICImagingFactory,
            nullptr,
            CLSCTX_INPROC_SERVER,
            IID_PPV_ARGS(wic_factory_.ReleaseAndGetAddressOf())
        );
    }

    UINT ReadGifFrameDelayMs(IWICBitmapFrameDecode* frame) {
        ComPtr<IWICMetadataQueryReader> metadata;
        HRESULT hr = frame->GetMetadataQueryReader(metadata.ReleaseAndGetAddressOf());
        if (FAILED(hr)) {
            return 100;
        }

        PROPVARIANT value;
        PropVariantInit(&value);
        hr = metadata->GetMetadataByName(L"/grctlext/Delay", &value);
        UINT delay_ms = 100;
        if (SUCCEEDED(hr) && value.vt == VT_UI2) {
            delay_ms = std::max<UINT>(10, static_cast<UINT>(value.uiVal) * 10);
        }
        PropVariantClear(&value);
        return delay_ms;
    }

    bool AdvanceGifFrame() {
        auto now = std::chrono::steady_clock::now();
        bool advanced = false;
        while (now >= gif_next_frame_at_) {
            gif_frame_index_ = (gif_frame_index_ + 1) % gif_frames_.size();
            gif_next_frame_at_ += std::chrono::milliseconds(
                gif_frame_delays_ms_[gif_frame_index_]
            );
            advanced = true;
        }
        return advanced;
    }

    struct VideoFrame {
        std::vector<BYTE> pixels;
        LONGLONG timestamp = 0;
        bool starts_loop = false;
    };

    HRESULT InitializeVideo() {
        if (g_options.file.empty()) {
            return E_INVALIDARG;
        }

        HRESULT hr = S_OK;
        if (!media_foundation_started_) {
            hr = MFStartup(MF_VERSION);
            if (FAILED(hr)) {
                return hr;
            }
            media_foundation_started_ = true;
        }

        ResetVideoPlaybackState();

        if (d3d_device_ && !disable_dxgi_video_) {
            HRESULT manager_hr = MFCreateDXGIDeviceManager(
                &dxgi_device_manager_token_,
                dxgi_device_manager_.ReleaseAndGetAddressOf()
            );
            if (SUCCEEDED(manager_hr)) {
                manager_hr = dxgi_device_manager_->ResetDevice(
                    d3d_device_.Get(),
                    dxgi_device_manager_token_
                );
                if (FAILED(manager_hr)) {
                    dxgi_device_manager_.Reset();
                    dxgi_device_manager_token_ = 0;
                }
            }
        }

        ComPtr<IMFAttributes> reader_attributes;
        hr = MFCreateAttributes(reader_attributes.ReleaseAndGetAddressOf(), 3);
        if (FAILED(hr)) {
            return hr;
        }
        if (dxgi_device_manager_) {
            hr = reader_attributes->SetUnknown(
                MF_SOURCE_READER_D3D_MANAGER,
                dxgi_device_manager_.Get()
            );
            if (FAILED(hr)) {
                dxgi_device_manager_.Reset();
                dxgi_device_manager_token_ = 0;
            }
        }
        hr = reader_attributes->SetUINT32(MF_SOURCE_READER_ENABLE_VIDEO_PROCESSING, TRUE);
        if (FAILED(hr)) {
            return hr;
        }
        hr = reader_attributes->SetUINT32(
            MF_READWRITE_ENABLE_HARDWARE_TRANSFORMS,
            disable_dxgi_video_ ? FALSE : TRUE
        );
        if (FAILED(hr)) {
            return hr;
        }

        hr = MFCreateSourceReaderFromURL(
            g_options.file.c_str(),
            reader_attributes.Get(),
            video_reader_.ReleaseAndGetAddressOf()
        );
        if (FAILED(hr) && dxgi_device_manager_) {
            PrintFailure(L"MFCreateSourceReaderFromURL hardware", hr);
            dxgi_device_manager_.Reset();
            dxgi_device_manager_token_ = 0;
            reader_attributes.Reset();
            hr = MFCreateAttributes(reader_attributes.ReleaseAndGetAddressOf(), 2);
            if (FAILED(hr)) {
                PrintFailure(L"MFCreateAttributes hardware no manager", hr);
                return hr;
            }
            hr = reader_attributes->SetUINT32(MF_SOURCE_READER_ENABLE_VIDEO_PROCESSING, TRUE);
            if (FAILED(hr)) {
                PrintFailure(L"MF_SOURCE_READER_ENABLE_VIDEO_PROCESSING hardware no manager", hr);
                return hr;
            }
            hr = reader_attributes->SetUINT32(MF_READWRITE_ENABLE_HARDWARE_TRANSFORMS, TRUE);
            if (FAILED(hr)) {
                PrintFailure(L"MF_READWRITE_ENABLE_HARDWARE_TRANSFORMS hardware no manager", hr);
                return hr;
            }
            hr = MFCreateSourceReaderFromURL(
                g_options.file.c_str(),
                reader_attributes.Get(),
                video_reader_.ReleaseAndGetAddressOf()
            );
            if (FAILED(hr)) {
                PrintFailure(L"MFCreateSourceReaderFromURL hardware no manager", hr);
            }
        }
        if (FAILED(hr)) {
            disable_dxgi_video_ = true;
            dxgi_device_manager_.Reset();
            dxgi_device_manager_token_ = 0;
            reader_attributes.Reset();
            hr = MFCreateAttributes(reader_attributes.ReleaseAndGetAddressOf(), 2);
            if (FAILED(hr)) {
                PrintFailure(L"MFCreateAttributes CPU fallback", hr);
                return hr;
            }
            hr = reader_attributes->SetUINT32(MF_SOURCE_READER_ENABLE_VIDEO_PROCESSING, TRUE);
            if (FAILED(hr)) {
                PrintFailure(L"MF_SOURCE_READER_ENABLE_VIDEO_PROCESSING CPU fallback", hr);
                return hr;
            }
            hr = reader_attributes->SetUINT32(MF_READWRITE_ENABLE_HARDWARE_TRANSFORMS, FALSE);
            if (FAILED(hr)) {
                PrintFailure(L"MF_READWRITE_ENABLE_HARDWARE_TRANSFORMS CPU fallback", hr);
                return hr;
            }
            hr = MFCreateSourceReaderFromURL(
                g_options.file.c_str(),
                reader_attributes.Get(),
                video_reader_.ReleaseAndGetAddressOf()
            );
        }
        if (FAILED(hr)) {
            PrintFailure(L"MFCreateSourceReaderFromURL", hr);
            return hr;
        }

        ComPtr<IMFMediaType> output_type;
        hr = MFCreateMediaType(output_type.ReleaseAndGetAddressOf());
        if (FAILED(hr)) {
            return hr;
        }
        hr = output_type->SetGUID(MF_MT_MAJOR_TYPE, MFMediaType_Video);
        if (FAILED(hr)) {
            return hr;
        }
        hr = output_type->SetGUID(MF_MT_SUBTYPE, MFVideoFormat_RGB32);
        if (FAILED(hr)) {
            return hr;
        }
        MFSetAttributeRatio(output_type.Get(), MF_MT_FRAME_RATE, std::max<UINT>(1, g_options.fps), 1);
        ComPtr<IMFMediaType> native_type;
        if (SUCCEEDED(video_reader_->GetNativeMediaType(
            static_cast<DWORD>(MF_SOURCE_READER_FIRST_VIDEO_STREAM),
            0,
            native_type.ReleaseAndGetAddressOf()
        ))) {
            UINT32 frame_rate_numerator = 0;
            UINT32 frame_rate_denominator = 0;
            if (
                SUCCEEDED(MFGetAttributeRatio(
                    native_type.Get(),
                    MF_MT_FRAME_RATE,
                    &frame_rate_numerator,
                    &frame_rate_denominator
                ))
                && frame_rate_numerator > 0
                && frame_rate_denominator > 0
            ) {
                const UINT native_fps = std::clamp(
                    static_cast<UINT>(
                        (frame_rate_numerator + frame_rate_denominator - 1)
                        / frame_rate_denominator
                    ),
                    1U,
                    kMaxCompositorFps
                );
                g_options.fps = std::min(g_options.fps, native_fps);
                if (native_fps > g_options.fps) {
                    video_output_interval_ = 10000000LL / std::max<UINT>(1, g_options.fps);
                } else {
                    video_output_interval_ = 0;
                }
            }
            UINT native_width = 0;
            UINT native_height = 0;
            if (
                SUCCEEDED(MFGetAttributeSize(
                    native_type.Get(),
                    MF_MT_FRAME_SIZE,
                    &native_width,
                    &native_height
                ))
                && native_width > 0
                && native_height > 0
            ) {
                const UINT max_decode_width = std::max<UINT>(320, std::min(g_options.video_max_width, kMaxVideoDecodeWidth));
                const UINT max_decode_height = std::max<UINT>(240, std::min(g_options.video_max_height, kMaxVideoDecodeHeight));
                const double width_scale = static_cast<double>(max_decode_width) / native_width;
                const double height_scale = static_cast<double>(max_decode_height) / native_height;
                const double scale = std::min(1.0, std::min(width_scale, height_scale));
                const UINT output_width = std::max<UINT>(
                    2,
                    static_cast<UINT>(native_width * scale) & ~1U
                );
                const UINT output_height = std::max<UINT>(
                    2,
                    static_cast<UINT>(native_height * scale) & ~1U
                );
                if (scale < 1.0) {
                    hr = MFSetAttributeSize(
                        output_type.Get(),
                        MF_MT_FRAME_SIZE,
                        output_width,
                        output_height
                    );
                    if (FAILED(hr)) {
                        return hr;
                    }
                }
            }
        }
        hr = video_reader_->SetCurrentMediaType(
            static_cast<DWORD>(MF_SOURCE_READER_FIRST_VIDEO_STREAM),
            nullptr,
            output_type.Get()
        );
        if (FAILED(hr)) {
            PrintFailure(L"SetCurrentMediaType sized", hr);
            output_type->DeleteItem(MF_MT_FRAME_RATE);
            hr = video_reader_->SetCurrentMediaType(
                static_cast<DWORD>(MF_SOURCE_READER_FIRST_VIDEO_STREAM),
                nullptr,
                output_type.Get()
            );
            if (FAILED(hr)) {
                PrintFailure(L"SetCurrentMediaType sized no fps", hr);
                output_type->DeleteItem(MF_MT_FRAME_SIZE);
                hr = video_reader_->SetCurrentMediaType(
                    static_cast<DWORD>(MF_SOURCE_READER_FIRST_VIDEO_STREAM),
                    nullptr,
                    output_type.Get()
                );
                if (FAILED(hr)) {
                    PrintFailure(L"SetCurrentMediaType fallback", hr);
                    return hr;
                }
            }
        }

        ComPtr<IMFMediaType> active_type;
        hr = video_reader_->GetCurrentMediaType(
            static_cast<DWORD>(MF_SOURCE_READER_FIRST_VIDEO_STREAM),
            active_type.ReleaseAndGetAddressOf()
        );
        if (FAILED(hr)) {
            PrintFailure(L"GetCurrentMediaType", hr);
            return hr;
        }
        hr = MFGetAttributeSize(active_type.Get(), MF_MT_FRAME_SIZE, &video_width_, &video_height_);
        if (FAILED(hr) || video_width_ == 0 || video_height_ == 0) {
            PrintFailure(L"MF_MT_FRAME_SIZE", FAILED(hr) ? hr : E_FAIL);
            return FAILED(hr) ? hr : E_FAIL;
        }

        hr = ReadVideoFrame(&video_current_frame_);
        if (FAILED(hr)) {
            PrintFailure(L"ReadVideoFrame initial", hr);
            return hr;
        }
        video_clock_started_at_ = std::chrono::steady_clock::now();
        video_clock_origin_ = video_current_frame_.timestamp;
        video_decode_thread_ = std::thread([this]() { VideoDecodeLoop(); });
        return S_OK;
    }

    HRESULT ReadVideoFrame(VideoFrame* frame) {
        if (!frame || !video_reader_) {
            return E_INVALIDARG;
        }

        bool starts_loop = false;
        for (;;) {
            DWORD flags = 0;
            LONGLONG timestamp = 0;
            ComPtr<IMFSample> sample;
            HRESULT hr = video_reader_->ReadSample(
                static_cast<DWORD>(MF_SOURCE_READER_FIRST_VIDEO_STREAM),
                0,
                nullptr,
                &flags,
                &timestamp,
                sample.ReleaseAndGetAddressOf()
            );
            if (FAILED(hr)) {
                return hr;
            }
            if (flags & MF_SOURCE_READERF_ENDOFSTREAM) {
                PROPVARIANT position;
                PropVariantInit(&position);
                position.vt = VT_I8;
                position.hVal.QuadPart = 0;
                hr = video_reader_->SetCurrentPosition(GUID_NULL, position);
                PropVariantClear(&position);
                if (FAILED(hr)) {
                    return hr;
                }
                starts_loop = true;
                continue;
            }
            if (!sample) {
                continue;
            }
            if (
                video_output_interval_ > 0
                && video_have_output_timestamp_
                && !starts_loop
                && timestamp < video_last_output_timestamp_ + video_output_interval_
            ) {
                continue;
            }

            ComPtr<IMFMediaBuffer> buffer;
            hr = sample->GetBufferByIndex(0, buffer.ReleaseAndGetAddressOf());
            if (FAILED(hr)) {
                return hr;
            }

            const DWORD expected = video_width_ * video_height_ * 4;
            frame->pixels.resize(expected);
            ComPtr<IMF2DBuffer> buffer_2d;
            if (SUCCEEDED(buffer.As(&buffer_2d))) {
                BYTE* scanline = nullptr;
                LONG stride = 0;
                hr = buffer_2d->Lock2D(&scanline, &stride);
                if (FAILED(hr)) {
                    return hr;
                }
                BYTE* destination = frame->pixels.data();
                const DWORD row_bytes = video_width_ * 4;
                BYTE* source_row = scanline;
                LONG source_stride = stride;
                if (stride < 0) {
                    source_row = scanline + static_cast<LONG>(video_height_ - 1) * (-stride);
                    source_stride = -stride;
                }
                for (UINT row = 0; row < video_height_; ++row) {
                    std::memcpy(
                        destination + row * row_bytes,
                        source_row + row * source_stride,
                        row_bytes
                    );
                }
                buffer_2d->Unlock2D();
                frame->timestamp = timestamp;
                frame->starts_loop = starts_loop;
                video_last_output_timestamp_ = timestamp;
                video_have_output_timestamp_ = true;
                return S_OK;
            }

            buffer.Reset();
            hr = sample->ConvertToContiguousBuffer(buffer.ReleaseAndGetAddressOf());
            if (FAILED(hr)) {
                return hr;
            }

            BYTE* source = nullptr;
            DWORD length = 0;
            hr = buffer->Lock(&source, nullptr, &length);
            if (FAILED(hr)) {
                return hr;
            }
            if (length < expected) {
                buffer->Unlock();
                return E_FAIL;
            }
            std::memcpy(frame->pixels.data(), source, expected);
            frame->timestamp = timestamp;
            frame->starts_loop = starts_loop;
            video_last_output_timestamp_ = timestamp;
            video_have_output_timestamp_ = true;
            buffer->Unlock();
            return S_OK;
        }
    }

    void VideoDecodeLoop() {
        HRESULT com_hr = CoInitializeEx(nullptr, COINIT_MULTITHREADED);
        bool should_uninitialize = SUCCEEDED(com_hr);
        SetThreadPriority(
            GetCurrentThread(),
            g_options.prefer_low_cpu ? THREAD_PRIORITY_LOWEST : THREAD_PRIORITY_BELOW_NORMAL
        );
        for (;;) {
            {
                std::unique_lock<std::mutex> lock(video_mutex_);
                video_condition_.wait(lock, [this]() {
                    return video_decoder_stopping_ || video_frames_.size() < kVideoQueueCapacity;
                });
                if (video_decoder_stopping_) {
                    if (should_uninitialize) {
                        CoUninitialize();
                    }
                    return;
                }
            }

            VideoFrame frame;
            {
                std::lock_guard<std::mutex> lock(video_mutex_);
                if (!video_recycled_buffers_.empty()) {
                    frame.pixels = std::move(video_recycled_buffers_.front());
                    video_recycled_buffers_.pop_front();
                }
            }
            HRESULT hr = ReadVideoFrame(&frame);
            if (FAILED(hr)) {
                PrintFailure(L"ReadVideoFrame async", hr);
                if (should_uninitialize) {
                    CoUninitialize();
                }
                return;
            }

            std::lock_guard<std::mutex> lock(video_mutex_);
            video_frames_.push_back(std::move(frame));
        }
    }

    void StopVideoDecoder() {
        {
            std::lock_guard<std::mutex> lock(video_mutex_);
            video_decoder_stopping_ = true;
        }
        video_condition_.notify_all();
        if (video_decode_thread_.joinable()) {
            video_decode_thread_.join();
        }
    }

    void ResetVideoPlaybackState() {
        std::lock_guard<std::mutex> lock(video_mutex_);
        video_decoder_stopping_ = false;
        video_reader_.Reset();
        dxgi_device_manager_.Reset();
        dxgi_device_manager_token_ = 0;
        video_current_frame_ = VideoFrame{};
        video_frames_.clear();
        video_recycled_buffers_.clear();
        video_width_ = 0;
        video_height_ = 0;
        video_output_interval_ = 0;
        video_last_output_timestamp_ = 0;
        video_have_output_timestamp_ = false;
    }

    void RecycleCurrentVideoPixels() {
        if (
            !video_current_frame_.pixels.empty()
            && video_recycled_buffers_.size() < kVideoRecycleCapacity
        ) {
            video_recycled_buffers_.push_back(std::move(video_current_frame_.pixels));
        }
    }

    bool AdvanceVideoFrame() {
        auto now = std::chrono::steady_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::microseconds>(
            now - video_clock_started_at_
        ).count();
        LONGLONG playback_position = video_clock_origin_ + elapsed * 10;

        bool advanced = false;
        std::lock_guard<std::mutex> lock(video_mutex_);
        while (!video_frames_.empty()) {
            VideoFrame& next = video_frames_.front();
            if (next.starts_loop) {
                RecycleCurrentVideoPixels();
                video_current_frame_ = std::move(next);
                video_frames_.pop_front();
                video_clock_started_at_ = now;
                video_clock_origin_ = video_current_frame_.timestamp;
                advanced = true;
                break;
            }
            if (playback_position < next.timestamp) {
                break;
            }
            RecycleCurrentVideoPixels();
            video_current_frame_ = std::move(next);
            video_frames_.pop_front();
            advanced = true;
        }
        if (advanced) {
            video_condition_.notify_one();
        }
        return advanced;
    }

    HWND hwnd_ = nullptr;
    ComPtr<ID2D1Factory> d2d_factory_;
    ComPtr<ID3D11Device> d3d_device_;
    ComPtr<IDCompositionDevice> dcomp_device_;
    ComPtr<IDCompositionTarget> target_;
    ComPtr<IDCompositionVisual> visual_;
    ComPtr<IDCompositionSurface> surface_;
    ComPtr<IWICImagingFactory> wic_factory_;
    ComPtr<IWICFormatConverter> image_converter_;
    ComPtr<IMMDeviceEnumerator> audio_enumerator_;
    ComPtr<IAudioMeterInformation> audio_meter_;
    ComPtr<IMFDXGIDeviceManager> dxgi_device_manager_;
    UINT dxgi_device_manager_token_ = 0;
    std::vector<ComPtr<IWICFormatConverter>> gif_frames_;
    std::vector<UINT> gif_frame_delays_ms_;
    size_t gif_frame_index_ = 0;
    std::chrono::steady_clock::time_point gif_next_frame_at_{};
    ComPtr<IMFSourceReader> video_reader_;
    VideoFrame video_current_frame_;
    std::deque<VideoFrame> video_frames_;
    std::deque<std::vector<BYTE>> video_recycled_buffers_;
    std::thread video_decode_thread_;
    std::mutex video_mutex_;
    std::condition_variable video_condition_;
    UINT video_width_ = 0;
    UINT video_height_ = 0;
    LONGLONG video_output_interval_ = 0;
    LONGLONG video_last_output_timestamp_ = 0;
    LONGLONG video_clock_origin_ = 0;
    std::chrono::steady_clock::time_point video_clock_started_at_{};
    bool media_foundation_started_ = false;
    bool disable_dxgi_video_ = false;
    bool video_decoder_stopping_ = false;
    bool video_have_output_timestamp_ = false;
    bool rendered_once_ = false;
    UINT surface_width_ = 0;
    UINT surface_height_ = 0;
};

NativeCompositor g_compositor;

bool ParseHexColor(const wchar_t* text, D2D1_COLOR_F* color) {
    if (!text || !color || wcslen(text) != 7 || text[0] != L'#') {
        return false;
    }

    wchar_t* end = nullptr;
    unsigned long value = wcstoul(text + 1, &end, 16);
    if (!end || *end != L'\0') {
        return false;
    }

    color->r = static_cast<float>((value >> 16) & 0xFF) / 255.0f;
    color->g = static_cast<float>((value >> 8) & 0xFF) / 255.0f;
    color->b = static_cast<float>(value & 0xFF) / 255.0f;
    color->a = 1.0f;
    return true;
}

PreviewOptions ParseOptions() {
    PreviewOptions options;
    int argc = 0;
    LPWSTR* argv = CommandLineToArgvW(GetCommandLineW(), &argc);
    if (!argv) {
        return options;
    }

    for (int index = 1; index < argc; ++index) {
        if (wcscmp(argv[index], L"--fps") == 0 && index + 1 < argc) {
            options.fps = std::clamp(static_cast<UINT>(_wtoi(argv[++index])), 1U, kMaxCompositorFps);
        } else if (wcscmp(argv[index], L"--effect-intensity") == 0 && index + 1 < argc) {
            options.effect_intensity = std::clamp(static_cast<UINT>(_wtoi(argv[++index])), 0U, 100U);
        } else if (wcscmp(argv[index], L"--effect-speed") == 0 && index + 1 < argc) {
            options.effect_speed = std::clamp(static_cast<UINT>(_wtoi(argv[++index])), 10U, 200U);
        } else if (wcscmp(argv[index], L"--color") == 0 && index + 1 < argc) {
            ParseHexColor(argv[++index], &options.color);
        } else if (wcscmp(argv[index], L"--scene") == 0 && index + 1 < argc) {
            options.scene = argv[++index];
        } else if (wcscmp(argv[index], L"--file") == 0 && index + 1 < argc) {
            options.file = argv[++index];
        } else if (wcscmp(argv[index], L"--replace-existing") == 0) {
            options.replace_existing = true;
        } else if (wcscmp(argv[index], L"--prefer-low-cpu") == 0) {
            options.prefer_low_cpu = true;
        } else if (wcscmp(argv[index], L"--video-max-width") == 0 && index + 1 < argc) {
            options.video_max_width = std::clamp(static_cast<UINT>(_wtoi(argv[++index])), 320U, kMaxVideoDecodeWidth);
        } else if (wcscmp(argv[index], L"--video-max-height") == 0 && index + 1 < argc) {
            options.video_max_height = std::clamp(static_cast<UINT>(_wtoi(argv[++index])), 240U, kMaxVideoDecodeHeight);
        } else if (wcscmp(argv[index], L"--instance-key") == 0 && index + 1 < argc) {
            options.instance_key = argv[++index];
        } else if (wcscmp(argv[index], L"--x") == 0 && index + 1 < argc) {
            options.x = _wtoi(argv[++index]);
        } else if (wcscmp(argv[index], L"--y") == 0 && index + 1 < argc) {
            options.y = _wtoi(argv[++index]);
        } else if (wcscmp(argv[index], L"--width") == 0 && index + 1 < argc) {
            options.width = std::max(320, _wtoi(argv[++index]));
        } else if (wcscmp(argv[index], L"--height") == 0 && index + 1 < argc) {
            options.height = std::max(240, _wtoi(argv[++index]));
        } else if (wcscmp(argv[index], L"--fullscreen") == 0) {
            options.fullscreen = true;
        } else if (wcscmp(argv[index], L"--desktop-experimental") == 0) {
            options.desktop_experimental = true;
        } else if (wcscmp(argv[index], L"--desktop-live") == 0) {
            options.desktop_live = true;
        } else if (wcscmp(argv[index], L"--repeat-monitor") == 0 && index + 1 < argc) {
            int x = 0;
            int y = 0;
            int width = 0;
            int height = 0;
            if (
                swscanf_s(argv[++index], L"%d,%d,%d,%d", &x, &y, &width, &height) == 4
                && width > 0
                && height > 0
            ) {
                options.repeat_monitors.push_back(RECT{x, y, x + width, y + height});
            }
        }
    }

    LocalFree(argv);
    return options;
}

LRESULT CALLBACK WindowProc(HWND hwnd, UINT message, WPARAM wparam, LPARAM lparam) {
    switch (message) {
        case WM_SIZE: {
            UINT width = LOWORD(lparam);
            UINT height = HIWORD(lparam);
            if (width > 0 && height > 0 && g_compositor.IsInitialized()) {
                HRESULT hr = g_compositor.Render(width, height);
                if (FAILED(hr)) {
                    PrintFailure(L"Render", hr);
                }
            }
            return 0;
        }
        case WM_TIMER: {
            if (g_options.desktop_live && !IsDesktopHostValid(hwnd)) {
                DestroyWindow(hwnd);
                return 0;
            }
            RECT client_rect{};
            GetClientRect(hwnd, &client_rect);
            HRESULT hr = g_compositor.Render(
                static_cast<UINT>(client_rect.right - client_rect.left),
                static_cast<UINT>(client_rect.bottom - client_rect.top)
            );
            if (FAILED(hr)) {
                PrintFailure(L"Render", hr);
            }
            return 0;
        }
        case WM_DESTROY:
            KillTimer(hwnd, kAnimationTimer);
            PostQuitMessage(0);
            return 0;
        case WM_NCHITTEST:
            if (g_options.desktop_experimental || g_options.desktop_live) {
                return HTTRANSPARENT;
            }
            break;
        case WM_MOUSEACTIVATE:
            if (g_options.desktop_experimental || g_options.desktop_live) {
                return MA_NOACTIVATE;
            }
            break;
        default:
            return DefWindowProcW(hwnd, message, wparam, lparam);
    }
    return DefWindowProcW(hwnd, message, wparam, lparam);
}

}  // namespace

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, PWSTR, int show_command) {
    SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2);
    SetPriorityClass(GetCurrentProcess(), BELOW_NORMAL_PRIORITY_CLASS);
    SetThreadPriority(GetCurrentThread(), THREAD_PRIORITY_BELOW_NORMAL);
    HRESULT com_hr = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
    if (FAILED(com_hr)) {
        PrintFailure(L"CoInitializeEx", com_hr);
        return 1;
    }
    g_options = ParseOptions();
    std::wstring mutex_name = SingleInstanceMutex();
    std::wstring window_title = WindowTitle();
    HANDLE single_instance = nullptr;
    for (int attempt = 0; attempt < 20; ++attempt) {
        single_instance = CreateMutexW(nullptr, TRUE, mutex_name.c_str());
        if (!single_instance) {
            return 1;
        }
        if (GetLastError() != ERROR_ALREADY_EXISTS) {
            break;
        }
        HWND existing = FindWindowW(kWindowClass, window_title.c_str());
        if (!g_options.replace_existing) {
            if (existing) {
                ShowWindow(existing, SW_RESTORE);
                SetForegroundWindow(existing);
            }
            CloseHandle(single_instance);
            return 0;
        }
        if (existing && attempt == 0) {
            PostMessageW(existing, WM_CLOSE, 0, 0);
        }
        CloseHandle(single_instance);
        single_instance = nullptr;
        Sleep(100);
    }
    if (!single_instance) {
        return 1;
    }
    if (GetLastError() == ERROR_ALREADY_EXISTS) {
        HWND existing = FindWindowW(kWindowClass, window_title.c_str());
        if (existing) {
            ShowWindow(existing, SW_RESTORE);
            SetForegroundWindow(existing);
        }
        CloseHandle(single_instance);
        return 0;
    }

    WNDCLASSW window_class{};
    window_class.lpfnWndProc = WindowProc;
    window_class.hInstance = instance;
    window_class.lpszClassName = kWindowClass;
    window_class.hCursor = LoadCursorW(nullptr, MAKEINTRESOURCEW(32512));
    if (!RegisterClassW(&window_class)) {
        PrintFailure(L"RegisterClassW", HRESULT_FROM_WIN32(GetLastError()));
        return 1;
    }

    HWND hwnd = CreateWindowExW(
        0,
        kWindowClass,
        window_title.c_str(),
        (g_options.fullscreen || g_options.desktop_experimental || g_options.desktop_live)
            ? WS_POPUP
            : WS_OVERLAPPEDWINDOW,
        g_options.x,
        g_options.y,
        g_options.width,
        g_options.height,
        nullptr,
        nullptr,
        instance,
        nullptr
    );
    if (!hwnd) {
        PrintFailure(L"CreateWindowExW", HRESULT_FROM_WIN32(GetLastError()));
        return 1;
    }
    RECT client_rect{};
    GetClientRect(hwnd, &client_rect);
    UINT client_width = static_cast<UINT>(client_rect.right - client_rect.left);
    UINT client_height = static_cast<UINT>(client_rect.bottom - client_rect.top);
    if (client_width == 0 || client_height == 0) {
        client_width = static_cast<UINT>(std::max(1, g_options.width));
        client_height = static_cast<UINT>(std::max(1, g_options.height));
    }

    HRESULT hr = g_compositor.Initialize(
        hwnd,
        client_width,
        client_height
    );
    if (FAILED(hr)) {
        PrintFailure(L"NativeCompositor::Initialize", hr);
        if (!g_options.desktop_live) {
            std::wstring message = L"NativeCompositor::Initialize failed: " + HResultText(hr);
            MessageBoxW(hwnd, message.c_str(), window_title.c_str(), MB_OK | MB_ICONERROR);
        }
        DestroyWindow(hwnd);
        return 1;
    }

    if (
        g_options.desktop_experimental
        && !AttachToProgmanStack(
            hwnd,
            g_options.x,
            g_options.y,
            g_options.width,
            g_options.height
        )
    ) {
        MessageBoxW(
            hwnd,
            L"Desktop experimental attach failed: Progman/SHELLDLL_DefView stack is unavailable.",
            window_title.c_str(),
            MB_OK | MB_ICONERROR
        );
        DestroyWindow(hwnd);
        return 1;
    }
    if (
        g_options.desktop_live
        && !AttachToDesktop(
            hwnd,
            g_options.x,
            g_options.y,
            g_options.width,
            g_options.height
        )
    ) {
        PrintFailure(L"AttachToDesktop", HRESULT_FROM_WIN32(GetLastError()));
        DestroyWindow(hwnd);
        return 1;
    }

    ShowWindow(hwnd, show_command);
    UpdateWindow(hwnd);
    SetTimer(hwnd, kAnimationTimer, RenderTimerIntervalMs(), nullptr);

    MSG message{};
    while (GetMessageW(&message, nullptr, 0, 0) > 0) {
        TranslateMessage(&message);
        DispatchMessageW(&message);
    }
    CloseHandle(single_instance);
    CoUninitialize();
    return 0;
}
