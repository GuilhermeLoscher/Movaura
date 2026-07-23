# Partner Center runFullTrust justification - Movaura

Movaura is a packaged Win32 desktop application for Windows.

The package declares `runFullTrust` because the application needs to run the existing desktop executable and native helper processes used for local wallpaper presentation. The product integrates with the Windows desktop experience using normal user-context Win32 windows, monitor detection, tray controls and a native compositor.

The application uses this capability for:

- launching the packaged Win32 app entry point;
- managing local wallpaper/compositor windows;
- interacting with the desktop and monitor layout;
- presenting live wallpapers through native desktop composition helpers;
- tray icon and normal desktop lifecycle controls;
- starting and stopping helper executables bundled inside the package.

The application does not require:

- a kernel driver;
- a system service;
- mandatory administrator elevation at normal runtime;
- hidden persistence;
- unrestricted background execution outside user-visible wallpaper features;
- undisclosed data collection.

Movaura processes user media files locally by default. Network use, beta activation or future online features must be documented separately in the privacy policy and Store submission notes.

This is a technical justification for Microsoft Store review. It is not a legal guarantee of approval.
