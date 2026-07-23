import ctypes

import win32con
import win32gui


GWL_STYLE = win32con.GWL_STYLE
GWL_EXSTYLE = win32con.GWL_EXSTYLE
LWA_ALPHA = 0x00000002
_user32 = ctypes.windll.user32
_user32.SetLayeredWindowAttributes.argtypes = [
    ctypes.c_void_p,
    ctypes.c_uint32,
    ctypes.c_ubyte,
    ctypes.c_uint32,
]
_user32.SetLayeredWindowAttributes.restype = ctypes.c_int


def prepare_child_wallpaper(hwnd: int) -> None:
    style = win32gui.GetWindowLong(hwnd, GWL_STYLE)
    style &= ~win32con.WS_POPUP
    style &= ~win32con.WS_CAPTION
    style &= ~win32con.WS_THICKFRAME
    style |= win32con.WS_CHILD
    style |= win32con.WS_VISIBLE
    win32gui.SetWindowLong(hwnd, GWL_STYLE, style)

    ex_style = win32gui.GetWindowLong(hwnd, GWL_EXSTYLE)
    ex_style &= ~win32con.WS_EX_APPWINDOW
    ex_style |= win32con.WS_EX_TOOLWINDOW
    win32gui.SetWindowLong(hwnd, GWL_EXSTYLE, ex_style)


def prepare_overlay_wallpaper(hwnd: int) -> None:
    style = win32gui.GetWindowLong(hwnd, GWL_STYLE)
    style &= ~win32con.WS_CAPTION
    style &= ~win32con.WS_THICKFRAME
    style |= win32con.WS_POPUP
    style |= win32con.WS_VISIBLE
    win32gui.SetWindowLong(hwnd, GWL_STYLE, style)

    ex_style = win32gui.GetWindowLong(hwnd, GWL_EXSTYLE)
    ex_style &= ~win32con.WS_EX_APPWINDOW
    ex_style |= win32con.WS_EX_TOOLWINDOW
    win32gui.SetWindowLong(hwnd, GWL_EXSTYLE, ex_style)


def prepare_desktop_overlay(hwnd: int) -> None:
    style = win32gui.GetWindowLong(hwnd, GWL_STYLE)
    style &= ~win32con.WS_CAPTION
    style &= ~win32con.WS_THICKFRAME
    style |= win32con.WS_POPUP
    style |= win32con.WS_VISIBLE
    win32gui.SetWindowLong(hwnd, GWL_STYLE, style)

    ex_style = win32gui.GetWindowLong(hwnd, GWL_EXSTYLE)
    ex_style &= ~win32con.WS_EX_APPWINDOW
    ex_style |= win32con.WS_EX_TOOLWINDOW
    ex_style |= win32con.WS_EX_NOACTIVATE
    win32gui.SetWindowLong(hwnd, GWL_EXSTYLE, ex_style)

def prepare_clickthrough_desktop_overlay(hwnd: int) -> None:
    prepare_desktop_overlay(hwnd)
    ex_style = win32gui.GetWindowLong(hwnd, GWL_EXSTYLE)
    ex_style |= win32con.WS_EX_TRANSPARENT
    ex_style |= win32con.WS_EX_LAYERED
    ex_style |= win32con.WS_EX_NOACTIVATE
    win32gui.SetWindowLong(hwnd, GWL_EXSTYLE, ex_style)
    _user32.SetLayeredWindowAttributes(hwnd, 0, 255, LWA_ALPHA)
    refresh_frame(hwnd)


def place_child(hwnd: int, parent: int, x: int, y: int, width: int, height: int) -> None:
    prepare_child_wallpaper(hwnd)
    win32gui.SetParent(hwnd, parent)
    win32gui.MoveWindow(hwnd, x, y, width, height, True)
    refresh_frame(hwnd)


def place_child_front(hwnd: int, parent: int, x: int, y: int, width: int, height: int) -> None:
    prepare_child_wallpaper(hwnd)
    win32gui.SetParent(hwnd, parent)
    win32gui.MoveWindow(hwnd, x, y, width, height, True)
    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_TOP,
        x,
        y,
        width,
        height,
        win32con.SWP_SHOWWINDOW | win32con.SWP_FRAMECHANGED | win32con.SWP_NOACTIVATE,
    )


def place_child_after(
    hwnd: int,
    parent: int,
    insert_after: int,
    x: int,
    y: int,
    width: int,
    height: int,
) -> None:
    prepare_child_wallpaper(hwnd)
    win32gui.SetParent(hwnd, parent)
    win32gui.MoveWindow(hwnd, x, y, width, height, True)
    win32gui.SetWindowPos(
        hwnd,
        insert_after,
        x,
        y,
        width,
        height,
        win32con.SWP_SHOWWINDOW | win32con.SWP_FRAMECHANGED | win32con.SWP_NOACTIVATE,
    )


def place_overlay(hwnd: int, x: int, y: int, width: int, height: int) -> None:
    prepare_overlay_wallpaper(hwnd)
    win32gui.SetParent(hwnd, 0)
    win32gui.MoveWindow(hwnd, x, y, width, height, True)
    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_TOPMOST,
        x,
        y,
        width,
        height,
        win32con.SWP_SHOWWINDOW | win32con.SWP_FRAMECHANGED | win32con.SWP_NOACTIVATE,
    )


def place_desktop_overlay(hwnd: int, x: int, y: int, width: int, height: int) -> None:
    prepare_desktop_overlay(hwnd)
    win32gui.SetParent(hwnd, 0)
    win32gui.MoveWindow(hwnd, x, y, width, height, True)
    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_TOP,
        x,
        y,
        width,
        height,
        win32con.SWP_SHOWWINDOW
        | win32con.SWP_FRAMECHANGED
        | win32con.SWP_NOACTIVATE
        | win32con.SWP_NOOWNERZORDER,
    )

def place_clickthrough_desktop_overlay(
    hwnd: int,
    progman: int,
    x: int,
    y: int,
    width: int,
    height: int,
) -> None:
    prepare_clickthrough_desktop_overlay(hwnd)
    win32gui.SetParent(hwnd, 0)
    previous = win32gui.GetWindow(progman, win32con.GW_HWNDPREV) if progman else 0
    insert_after = previous or win32con.HWND_TOP
    win32gui.SetWindowPos(
        hwnd,
        insert_after,
        x,
        y,
        width,
        height,
        win32con.SWP_SHOWWINDOW
        | win32con.SWP_FRAMECHANGED
        | win32con.SWP_NOACTIVATE
        | win32con.SWP_NOOWNERZORDER,
    )
    win32gui.ShowWindow(hwnd, win32con.SW_SHOWNOACTIVATE)


def place_clickthrough_overlay_top(hwnd: int, x: int, y: int, width: int, height: int) -> None:
    prepare_clickthrough_desktop_overlay(hwnd)
    win32gui.SetParent(hwnd, 0)
    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_TOP,
        x,
        y,
        width,
        height,
        win32con.SWP_SHOWWINDOW
        | win32con.SWP_FRAMECHANGED
        | win32con.SWP_NOACTIVATE
        | win32con.SWP_NOOWNERZORDER,
    )
    win32gui.ShowWindow(hwnd, win32con.SW_SHOWNOACTIVATE)


def describe_clickthrough_z_order(hwnd: int, progman: int) -> str:
    previous = win32gui.GetWindow(progman, win32con.GW_HWNDPREV) if progman else 0
    next_window = win32gui.GetWindow(hwnd, win32con.GW_HWNDNEXT)
    previous_window = win32gui.GetWindow(hwnd, win32con.GW_HWNDPREV)
    return (
        f"clickthrough z-order: hwnd={hwnd} progman={progman} "
        f"expected_previous={previous} actual_previous={previous_window} actual_next={next_window}"
    )


def keep_desktop_overlay_bottom(hwnd: int, x: int, y: int, width: int, height: int) -> None:
    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_BOTTOM,
        x,
        y,
        width,
        height,
        win32con.SWP_SHOWWINDOW
        | win32con.SWP_FRAMECHANGED
        | win32con.SWP_NOACTIVATE
        | win32con.SWP_NOOWNERZORDER,
    )


def refresh_frame(hwnd: int) -> None:
    win32gui.SetWindowPos(
        hwnd,
        0,
        0,
        0,
        0,
        0,
        win32con.SWP_NOMOVE
        | win32con.SWP_NOSIZE
        | win32con.SWP_NOZORDER
        | win32con.SWP_SHOWWINDOW
        | win32con.SWP_FRAMECHANGED,
    )
