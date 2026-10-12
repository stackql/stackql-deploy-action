import io
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest
import zipfile

import yaml


ROOT = Path(__file__).resolve().parents[1]
INSTALL = yaml.safe_load((ROOT / "action.yml").read_text(encoding="utf-8"))["runs"]["steps"][0]["run"]
BASE_URL = "https://github.com/stackql/stackql-deploy-rs/releases/latest/download"
BINARY = b'''#!/usr/bin/env bash
printf '%s\n' "$*" >> "$BINARY_LOG"
if [ "$1" = "info" ]; then exit "${MOCK_INFO_STATUS:-0}"; fi
echo 'stackql-deploy 2.3.0'
'''
MOCKS = r'''
export PROCESSOR_ARCHITECTURE="$MOCK_PROCESSOR_ARCHITECTURE"
export PROCESSOR_ARCHITEW6432="$MOCK_PROCESSOR_ARCHITEW6432"
uname() {
  case "$1" in
    -s) echo "$MOCK_OS" ;;
    -m) echo "$MOCK_ARCH" ;;
    *) return 1 ;;
  esac
}
powershell.exe() {
  printf '%s\n' "$*" >> "$POWERSHELL_LOG"
  [ -n "$MOCK_WINDOWS_ARCH" ] || return 1
  printf '%s\r\n' "$MOCK_WINDOWS_ARCH"
}
curl() {
  local url="${@: -1}"
  echo "$url" >> "$DOWNLOAD_LOG"
  [ "$MOCK_DOWNLOAD_STATUS" = 0 ] || return "$MOCK_DOWNLOAD_STATUS"
  if [ "$2" = '-o' ]; then
    cp "$ARCHIVES/${url##*/}" "$3"
  else
    cat "$ARCHIVES/${url##*/}"
  fi
}
if [ -n "${PREINSTALLED_DIR:-}" ]; then
  export PATH="$(cd "$PREINSTALLED_DIR" && pwd):$PATH"
fi
'''


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="deploy install ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = self.root / "workspace with spaces"
        self.workspace.mkdir()
        self.archives = self.root / "archives"
        self.archives.mkdir()
        for platform in ("linux-x86_64", "linux-arm64", "macos-universal"):
            with tarfile.open(self.archives / f"stackql-deploy-{platform}.tar.gz", "w:gz") as archive:
                member = tarfile.TarInfo("stackql-deploy")
                member.size = len(BINARY)
                member.mode = 0o644
                archive.addfile(member, io.BytesIO(BINARY))
        for arch in ("x86_64", "arm64"):
            with zipfile.ZipFile(self.archives / f"stackql-deploy-windows-{arch}.zip", "w") as archive:
                archive.writestr("stackql-deploy.exe", BINARY)
        self.script = self.root / "install.sh"
        self.script.write_text(MOCKS + INSTALL, encoding="utf-8", newline="\n")
        self.env = {
            **os.environ,
            "PATH": "/usr/bin:/bin",
            "GITHUB_WORKSPACE": self.workspace.as_posix(),
            "GITHUB_PATH": (self.root / "github_path").as_posix(),
            "ARCHIVES": self.archives.as_posix(),
            "DOWNLOAD_LOG": (self.root / "downloads").as_posix(),
            "BINARY_LOG": (self.root / "binary_calls").as_posix(),
            "POWERSHELL_LOG": (self.root / "powershell_calls").as_posix(),
            "MOCK_WINDOWS_ARCH": "",
            "PROCESSOR_ARCHITECTURE": "",
            "PROCESSOR_ARCHITEW6432": "",
            "MOCK_DOWNLOAD_STATUS": "0",
            "MOCK_INFO_STATUS": "0",
            "PREINSTALLED_DIR": "",
        }

    def install(self, system, arch, **env):
        for name in ("stackql-deploy", "stackql-deploy.exe", "stackql-deploy.zip"):
            (self.workspace / name).unlink(missing_ok=True)
        return subprocess.run(
            [shutil.which("bash"), "--noprofile", "--norc", "-e", "-o", "pipefail", self.script.as_posix()],
            cwd=self.workspace,
            env={
                **self.env, "MOCK_OS": system, "MOCK_ARCH": arch, **env,
                "MOCK_PROCESSOR_ARCHITECTURE": env.get("PROCESSOR_ARCHITECTURE", ""),
                "MOCK_PROCESSOR_ARCHITEW6432": env.get("PROCESSOR_ARCHITEW6432", ""),
            },
            text=True,
            capture_output=True,
        )

    def assert_install(self, system, arch, asset, **env):
        result = self.install(system, arch, **env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.root / "downloads").read_text().splitlines()[-1], f"{BASE_URL}/{asset}")
        binary = "stackql-deploy.exe" if asset.endswith(".zip") else "stackql-deploy"
        self.assertEqual((self.workspace / binary).read_bytes(), BINARY)
        self.assertIn("info", (self.root / "binary_calls").read_text().splitlines())
        self.assertEqual((self.root / "github_path").read_text().splitlines()[-1], self.workspace.as_posix())
        self.assertFalse((self.workspace / "stackql-deploy.zip").exists())

    def test_linux_and_macos_architectures(self):
        for system, arch, platform in (
            ("Linux", "x86_64", "linux-x86_64"),
            ("Linux", "amd64", "linux-x86_64"),
            ("Linux", "aarch64", "linux-arm64"),
            ("Linux", "arm64", "linux-arm64"),
            ("Darwin", "x86_64", "macos-universal"),
            ("Darwin", "arm64", "macos-universal"),
        ):
            with self.subTest(system=system, arch=arch):
                self.assert_install(system, arch, f"stackql-deploy-{platform}.tar.gz")
        self.assertFalse((self.root / "powershell_calls").exists())

    def test_windows_native_architecture(self):
        for system in ("MINGW64_NT-10.0", "MSYS_NT-10.0", "CYGWIN_NT-10.0", "Windows_NT"):
            for native, asset_arch in (("AMD64", "x86_64"), ("ARM64", "arm64")):
                with self.subTest(system=system, native=native):
                    self.assert_install(
                        system, "x86_64", f"stackql-deploy-windows-{asset_arch}.zip",
                        MOCK_WINDOWS_ARCH=native,
                        PROCESSOR_ARCHITECTURE="AMD64",
                        PROCESSOR_ARCHITEW6432="AMD64",
                    )
        self.assertIn("Get-ItemProperty", (self.root / "powershell_calls").read_text())

    def test_windows_architecture_fallbacks(self):
        for arch, env, expected in (
            ("x86_64", {"PROCESSOR_ARCHITEW6432": "ARM64", "PROCESSOR_ARCHITECTURE": "AMD64"}, "arm64"),
            ("x86_64", {"PROCESSOR_ARCHITECTURE": "ARM64"}, "arm64"),
            ("x86_64", {"PROCESSOR_ARCHITECTURE": "AMD64"}, "x86_64"),
            ("aarch64", {}, "arm64"),
            ("x86_64", {}, "x86_64"),
        ):
            with self.subTest(arch=arch, env=env):
                self.assert_install("MINGW64_NT-10.0", arch, f"stackql-deploy-windows-{expected}.zip", **env)

    def test_unsupported_platforms_do_not_download(self):
        for system, arch in (("Linux", "riscv64"), ("Darwin", "ppc"), ("MINGW32_NT-10.0", "i686"), ("FreeBSD", "x86_64")):
            with self.subTest(system=system, arch=arch):
                result = self.install(system, arch)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Unsupported platform", result.stderr)
                self.assertFalse((self.root / "downloads").exists())
                self.assertFalse((self.root / "github_path").exists())

    def test_download_failures_stop_installation(self):
        for system in ("Linux", "MINGW64_NT-10.0"):
            with self.subTest(system=system):
                result = self.install(system, "x86_64", MOCK_DOWNLOAD_STATUS="22")
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((self.root / "binary_calls").exists())
                self.assertFalse((self.root / "github_path").exists())

    def test_corrupt_archives_stop_installation(self):
        for system, asset in (("Linux", "linux-x86_64.tar.gz"), ("MINGW64_NT-10.0", "windows-x86_64.zip")):
            with self.subTest(system=system):
                (self.archives / f"stackql-deploy-{asset}").write_bytes(b"invalid archive")
                result = self.install(system, "x86_64")
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((self.root / "binary_calls").exists())
                self.assertFalse((self.root / "github_path").exists())

    def test_info_failure_is_propagated(self):
        result = self.install("Linux", "x86_64", MOCK_INFO_STATUS="9")
        self.assertEqual(result.returncode, 9, result.stdout + result.stderr)

    def test_existing_install_is_reused(self):
        installed = self.root / "existing install"
        installed.mkdir()
        binary = installed / "stackql-deploy"
        binary.write_bytes(BINARY)
        binary.chmod(0o755)
        result = self.install("Linux", "x86_64", PREINSTALLED_DIR=installed.as_posix())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("already installed", result.stdout)
        self.assertFalse((self.root / "downloads").exists())
        self.assertEqual((self.root / "binary_calls").read_text().splitlines(), ["--version"])


if __name__ == "__main__":
    unittest.main()
