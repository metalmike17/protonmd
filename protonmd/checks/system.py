"""System-wide checks: GPU stack, kernel limits, 32-bit libs."""
import os
import platform
import re
import resource
import shutil
import subprocess

from ..model import Fix, Result, Status


IN_FLATPAK = os.path.exists("/.flatpak-info")
HOST = "/run/host" if IN_FLATPAK else ""  # --filesystem=host-os:ro exposes the host's /usr here


def _run(cmd, timeout=15):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout
    except (OSError, subprocess.TimeoutExpired):
        return None, ""


def check_vulkan():
    if not shutil.which("vulkaninfo") and IN_FLATPAK:
        return Result("vulkan", "Vulkan 64-bit", Status.INFO,
                      "Can't run vulkaninfo from inside the Flatpak sandbox. Run it in a terminal to verify.")
    if not shutil.which("vulkaninfo"):
        return Result("vulkan", "Vulkan tools", Status.WARN,
                      "vulkaninfo not found, so Vulkan can't be verified.",
                      hint="Install vulkan-tools (Arch: sudo pacman -S vulkan-tools).")
    rc, out = _run(["vulkaninfo", "--summary"])
    devs = re.findall(r"deviceName\s*=\s*(.+)", out)
    types = re.findall(r"deviceType\s*=\s*PHYSICAL_DEVICE_TYPE_(\w+)", out)
    if rc != 0 or not devs:
        return Result("vulkan", "Vulkan 64-bit", Status.FAIL,
                      "vulkaninfo found no usable GPU.",
                      hint="Install your GPU's Vulkan driver (nvidia-utils / vulkan-radeon / vulkan-intel).")
    real = [d for d, t in zip(devs, types) if t != "CPU"] or devs
    cpu_only = all(t == "CPU" for t in types) if types else False
    if cpu_only:
        return Result("vulkan", "Vulkan 64-bit", Status.FAIL,
                      "Only a software renderer (llvmpipe) is available; games will be extremely slow.",
                      hint="Your GPU's Vulkan driver is missing or not loading.")
    return Result("vulkan", "Vulkan 64-bit", Status.OK, ", ".join(real))


def _glob_any(patterns):
    import glob
    return any(glob.glob(p) for p in patterns)


def check_vulkan_32_sandbox():
    has32 = _glob_any([f"{HOST}/usr/lib32/libvulkan.so.1", f"{HOST}/usr/lib/i386-linux-gnu/libvulkan.so.1"])
    nv = os.path.exists("/proc/driver/nvidia/version")
    nv32 = _glob_any([f"{HOST}/usr/lib32/libGLX_nvidia.so.0", f"{HOST}/usr/lib32/libnvidia-glcore.so*",
                      f"{HOST}/usr/lib/i386-linux-gnu/libGLX_nvidia.so.0"])
    if not has32:
        return Result("vulkan32", "32-bit Vulkan loader", Status.FAIL,
                      "No 32-bit libvulkan found on the host.",
                      hint="Enable [multilib] and install lib32-vulkan-icd-loader plus your driver's lib32 package.")
    if nv and not nv32:
        return Result("vulkan32_nv", "32-bit NVIDIA driver", Status.FAIL,
                      "NVIDIA GPU present but no 32-bit NVIDIA libraries found on the host.",
                      hint="Install lib32-nvidia-utils (match your driver package).")
    return Result("vulkan32", "32-bit Vulkan", Status.OK, "32-bit loader present.")


def check_vulkan_32():
    if IN_FLATPAK:
        return check_vulkan_32_sandbox()
    rc, out = _run(["ldconfig", "-p"])
    lines = [l for l in out.splitlines() if "libvulkan.so.1" in l]
    has32 = any("x86-64" not in l and "libc6" in l for l in lines)
    nv = shutil.which("nvidia-smi") is not None
    nv32 = any("libnvidia-glcore" in l or "libGLX_nvidia" in l for l in
               out.splitlines() if "x86-64" not in l and "libc6" in l)
    if not has32:
        return Result("vulkan32", "32-bit Vulkan loader", Status.FAIL,
                      "No 32-bit libvulkan found. 32-bit games and some launchers will fail to start.",
                      hint="Enable [multilib] and install lib32-vulkan-icd-loader plus your driver's lib32 package.")
    if nv and not nv32:
        return Result("vulkan32_nv", "32-bit NVIDIA driver", Status.FAIL,
                      "NVIDIA GPU present but no 32-bit NVIDIA libraries found.",
                      hint="Install lib32-nvidia-utils (match your driver package).")
    return Result("vulkan32", "32-bit Vulkan", Status.OK, "32-bit loader present.")


def check_gpu_driver():
    if IN_FLATPAK:
        try:
            ver = open("/proc/driver/nvidia/version").read().splitlines()[0]
            m = re.search(r"\b(\d{3}\.\d+(?:\.\d+)?)\b", ver)
            return Result("gpu", "GPU driver", Status.OK, f"NVIDIA kernel module {m.group(1) if m else '(unknown version)'}")
        except OSError:
            pass
        rc, out = _run(["sh", "-c", "cat /sys/class/drm/card*/device/driver/module/drivers 2>/dev/null; ls /sys/module | grep -E '^(amdgpu|i915|xe|nouveau)$'"])
        names = sorted(set(out.split()))
        return Result("gpu", "GPU driver", Status.OK if names else Status.INFO,
                      f"Kernel driver: {', '.join(names)}" if names else "Couldn't identify the GPU driver from the sandbox.")
    if shutil.which("nvidia-smi"):
        rc, out = _run(["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"])
        if rc == 0 and out.strip():
            return Result("gpu", "GPU driver", Status.OK, "NVIDIA " + out.strip().splitlines()[0])
        return Result("gpu", "GPU driver", Status.FAIL,
                      "nvidia-smi failed. The kernel module may not match the userspace driver.",
                      hint="Reboot after a driver update, or reinstall nvidia-utils and the kernel module.")
    rc, out = _run(["sh", "-c", "lspci -nnk | grep -A3 -Ei 'vga|3d'"])
    drv = re.findall(r"Kernel driver in use:\s*(\S+)", out)
    return Result("gpu", "GPU driver", Status.OK if drv else Status.WARN,
                  f"Kernel driver: {', '.join(drv)}" if drv else "Couldn't identify the GPU driver.")


def check_max_map_count():
    try:
        v = int(open("/proc/sys/vm/max_map_count").read())
    except OSError:
        return Result("mapcount", "vm.max_map_count", Status.INFO, "Unreadable.")
    if v < 1048576:
        return Result("mapcount", "vm.max_map_count", Status.WARN,
                      f"{v} is low. Games like Hogwarts Legacy, DayZ and Star Citizen crash with it.",
                      hint="sudo sysctl -w vm.max_map_count=2147483642, and persist it in /etc/sysctl.d/.")
    return Result("mapcount", "vm.max_map_count", Status.OK, str(v))


def check_nofile():
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    if hard < 524288:
        return Result("nofile", "Open file limit (esync)", Status.WARN,
                      f"Hard limit is {hard}. Esync needs 524288 or more.",
                      hint="Set DefaultLimitNOFILE=1048576 in /etc/systemd/system.conf.")
    return Result("nofile", "Open file limit (esync)", Status.OK, f"hard limit {hard}")


def check_kernel():
    rel = platform.release()
    sched = ""
    try:
        sched = open("/sys/kernel/sched_ext/state").read().strip()
    except OSError:
        pass
    extra = f", sched_ext: {sched}" if sched else ""
    return Result("kernel", "Kernel", Status.INFO, f"{rel}{extra}")


def check_gamemode():
    if IN_FLATPAK:
        found = _glob_any([f"{HOST}/usr/bin/gamemoderun"])
        return Result("gamemode", "GameMode", Status.OK if found else Status.INFO,
                      "Installed" if found else "Not installed (optional).",
                      hint="" if found else "Install gamemode and lib32-gamemode, then use gamemoderun %command%.")
    if not shutil.which("gamemoderun"):
        return Result("gamemode", "GameMode", Status.INFO, "Not installed (optional).",
                      hint="Install gamemode and lib32-gamemode, then use gamemoderun %command%.")
    rc, _ = _run(["systemctl", "--user", "is-active", "--quiet", "gamemoded"])
    return Result("gamemode", "GameMode", Status.OK, "Installed" + ("" if rc == 0 else " (daemon starts on demand)"))


def check_wine_deps():
    if IN_FLATPAK:
        miss = [t for t in ("winetricks", "protontricks") if not os.path.exists(f"{HOST}/usr/bin/{t}")]
        return Result("tricks", "Winetricks / Protontricks", Status.INFO if miss else Status.OK,
                      f"Not installed on the host: {', '.join(miss)}." if miss else "Both installed.")
    miss = [t for t in ("winetricks", "protontricks") if not shutil.which(t)]
    if miss:
        return Result("tricks", "Winetricks / Protontricks", Status.INFO,
                      f"Not installed: {', '.join(miss)}. Needed to install runtimes like vcredist into prefixes.")
    return Result("tricks", "Winetricks / Protontricks", Status.OK, "Both installed.")


ALL = [check_gpu_driver, check_vulkan, check_vulkan_32, check_max_map_count,
       check_nofile, check_kernel, check_gamemode, check_wine_deps]


def run_all():
    out = []
    for fn in ALL:
        try:
            out.append(fn())
        except Exception as e:  # a broken check must never take the app down
            out.append(Result(fn.__name__, fn.__name__, Status.INFO, f"Check crashed: {e}"))
    return out
