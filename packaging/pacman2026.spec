Name:           pacman2026
Version:        1.0.0
Release:        1%{?dist}
Summary:        Desktop maze chase game with original sound effects
License:        MIT
URL:            https://github.com/alkhusnetdinov79-tech/Pacman2026
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
Requires:       python3 >= 3.6
Requires:       python3-tkinter
Requires:       alsa-utils
# Ship source only. Avoid build-host Python bytecode and automatic dependencies.
AutoReqProv:    no
%global debug_package %{nil}
%global __os_install_post %{nil}

%description
An original Pacman-style arcade game with four ghosts, power pellets,
multiple levels, a persistent high score and synthesized sound effects.
Runs on Python 3.6+ and Tk 8.6. Intended for RED OS 8 / RHEL 8 desktops.

%prep
%setup -q

%build
# Pure Python; no architecture-specific compilation required.

%install
mkdir -p %{buildroot}%{_datadir}/%{name}/pacman2026
cp pacman2026/*.py %{buildroot}%{_datadir}/%{name}/pacman2026/
cp packaging/run.py %{buildroot}%{_datadir}/%{name}/run.py
cp -r assets %{buildroot}%{_datadir}/%{name}/assets
install -D -m 0755 packaging/pacman2026 %{buildroot}%{_bindir}/pacman2026
install -D -m 0644 packaging/pacman2026.desktop %{buildroot}%{_datadir}/applications/pacman2026.desktop
install -D -m 0644 assets/pacman2026.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/pacman2026.svg

%files
%license LICENSE
%doc README.md
%{_bindir}/pacman2026
%{_datadir}/%{name}/
%{_datadir}/applications/pacman2026.desktop
%{_datadir}/icons/hicolor/scalable/apps/pacman2026.svg

%changelog
* Sat Oct 10 2026 Pacman2026 contributors - 1.0.0-1
- Initial desktop game release.
