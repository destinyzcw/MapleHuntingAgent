# UU远程 integration on macOS

Status: design only. No window-capture or input-injection adapter exists yet.

## Capture

Identify UU远程 by application and selected window, then locate the game viewport inside it. Exclude toolbars, borders, letterboxing, and local overlays. Retain the uncropped frame for diagnosis alongside the game crop when practical.

Record window identity, position, logical size, capture pixel size, and viewport bounds. Mac Retina pixels and desktop input points can differ, as can remote resolution and displayed viewport resolution. The mapping must be established from the actual session, not assumed from a screenshot's dimensions.

macOS Screen Recording permission will be required for capture. The exact capture library and API will be selected during the first Mac capture milestone.

## Input

Local keyboard/mouse events must go to the intended UU远程 window. Capture and input coordinates must share an explicit transform. Record actual key bindings, keyboard layout, remote key forwarding, and how UU远程 handles held keys.

An executor must recheck focus before input, limit every hold duration, track the keys/buttons it owns, and release them on completion, interruption, timeout, or exception. macOS Accessibility permission will be required for input automation.

## Transport delay and stale frames

Measure capture delay and remote input-to-visible-effect delay before choosing loop timing. A later local capture timestamp alone does not prove a newer remote frame: a frozen remote stream can produce repeated images. Connection/freeze detection and state freshness must consider visual progress and transport indicators too.

## First integration checklist

1. Record the Mac/macOS and UU远程 versions.
2. Capture a window and inspect its viewport at the actual display scale.
3. Verify capture while focused/unfocused, resized, and disconnected.
4. Record a user-performed move and measure its visible delay.
5. Implement bounded input with a user interrupt and guaranteed release.
6. Verify a neutral input and a short movement before hunting actions.

The design does not require access to the remote computer's filesystem or game process.
