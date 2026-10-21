"""Built-in knowledge base. Each rule is plain data so it is easy to extend."""
import re

# Environment variables in launch options that commonly cause trouble.
# (regex on launch options, status name, message, hint)
LAUNCH_OPTION_RULES = [
    (r"\bPROTON_USE_WINED3D=1", "WARN",
     "PROTON_USE_WINED3D=1 replaces DXVK/VKD3D with OpenGL translation. It is much slower and rarely needed on modern GPUs.",
     "Remove it unless this game specifically needs it."),
    (r"\bPROTON_NO_ESYNC=1", "INFO",
     "Esync is disabled, which can cost performance. This was usually a workaround for old file limit issues.",
     "Remove it if the open file limit check passes."),
    (r"\bPROTON_NO_FSYNC=1", "INFO",
     "Fsync is disabled, which can cost performance. This only helps on kernels without futex2.",
     "Remove it unless it fixes a specific crash."),
    (r"\bDXVK_ASYNC=1", "WARN",
     "DXVK_ASYNC only works in patched DXVK builds. Mainline DXVK ignores it, and it can trigger anti-cheat bans in some online games.",
     "Remove it. Use shader pre-caching instead."),
    (r"\bPROTON_FORCE_LARGE_ADDRESS_AWARE=0", "WARN",
     "Disabling large-address-aware can cause out-of-memory crashes in 32-bit games.", ""),
    (r"\bVK_ICD_FILENAMES=", "WARN",
     "VK_ICD_FILENAMES is deprecated and can pin the game to a wrong or missing GPU driver after updates.",
     "Remove it, or use VK_DRIVER_FILES if you really need to pin a driver."),
    (r"\bWINEDLLOVERRIDES=", "INFO",
     "A custom WINEDLLOVERRIDES is set. Check it still applies, because stale overrides cause missing-DLL or black-screen bugs.", ""),
    (r"%command%\s*$", None, None, None),  # sentinel, handled in code
]

# Known fatal strings in Proton logs (PROTON_LOG=1 -> ~/steam-<appid>.log).
LOG_SIGNATURES = [
    (r"err:module:import_dll Library (\S+\.dll)", "Missing DLL: {0}",
     "A runtime is missing from the prefix. Install it with protontricks (for example vcrun2022, d3dcompiler_47, dotnet)."),
    (r"vkCreateInstance failed|Failed to create Vulkan instance|No Vulkan device", "Vulkan could not initialise",
     "Check the Vulkan 64-bit and 32-bit results above."),
    (r"err:virtual:map_view.*(?:0xc0000017|STATUS_NO_MEMORY)|Out of memory", "Out-of-memory error",
     "Raise vm.max_map_count, or the game ran out of 32-bit address space."),
    (r"wine: could not load kernel32\.dll|wine: failed to open", "Wine prefix is broken",
     "Back up and recreate the prefix with the fix below."),
    (r"Unhandled exception: page fault", "Game crashed with a page fault",
     "Try a different Proton version for this game."),
    (r"EasyAntiCheat|BattlEye", "Anti-cheat detected",
     "Some anti-cheats need the game's EAC/BattlEye runtime enabled by the developer for Linux, and not all do."),
]
