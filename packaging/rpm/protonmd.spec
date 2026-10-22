Name:           protonmd
Version:        0.1.3
Release:        1%{?dist}
Summary:        Diagnose why Linux games won't run
License:        GPL-3.0-or-later
URL:            https://github.com/metalmike17/protonmd
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
Requires:       python3 >= 3.10
Requires:       python3-gobject
Requires:       gtk4
Requires:       libadwaita
Recommends:     vulkan-tools
Suggests:       gamemode
Suggests:       winetricks

%description
ProtonMD checks GPU drivers, Vulkan setup and kernel limits, then inspects
each Steam game's Wine prefix, Proton version, launch options and shader
cache. It explains what is wrong and offers confirmed fixes.
Unofficial. Not affiliated with Valve or Proton AG.

%prep
%autosetup -n %{name}-%{version}

%build

%install
install -d %{buildroot}%{_datadir}/protonmd %{buildroot}%{_bindir}
cp -r protonmd %{buildroot}%{_datadir}/protonmd/
find %{buildroot} -name __pycache__ -prune -exec rm -rf {} +
cat > %{buildroot}%{_bindir}/protonmd <<'LAUNCH'
#!/usr/bin/python3
import sys
sys.path.insert(0, "/usr/share/protonmd")
from protonmd.launcher import main
sys.exit(main())
LAUNCH
chmod 755 %{buildroot}%{_bindir}/protonmd
install -Dm644 data/io.github.metalmike17.ProtonMD.desktop -t %{buildroot}%{_datadir}/applications/
install -Dm644 data/io.github.metalmike17.ProtonMD.metainfo.xml -t %{buildroot}%{_datadir}/metainfo/
install -Dm644 data/io.github.metalmike17.ProtonMD.svg -t %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/

%files
%license LICENSE
%{_bindir}/protonmd
%{_datadir}/protonmd/
%{_datadir}/applications/io.github.metalmike17.ProtonMD.desktop
%{_datadir}/metainfo/io.github.metalmike17.ProtonMD.metainfo.xml
%{_datadir}/icons/hicolor/scalable/apps/io.github.metalmike17.ProtonMD.svg

%changelog
* Wed Oct 21 2026 metalmike17 <michaeljg0717@gmail.com> - 0.1.3-1
- Initial RPM package
