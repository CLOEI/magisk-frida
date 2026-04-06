#!/usr/bin/env python3
import logging
import os
from pathlib import Path
import shutil
import subprocess
import zipfile
import json
import re

PATH_BASE = Path(__file__).parent.resolve()
PATH_BASE_MODULE: Path = PATH_BASE.joinpath("base")
PATH_BUILD: Path = PATH_BASE.joinpath("build")
PATH_BUILD_TMP: Path = PATH_BUILD.joinpath("tmp")
PATH_DOWNLOADS: Path = PATH_BASE.joinpath("downloads")

# NDK arch name -> module arch name
ARCH_MAP = {
    "arm64-v8a": "arm64",
    "armeabi-v7a": "arm",
    "x86": "x86",
}

logger = logging.getLogger()
syslog = logging.StreamHandler()
formatter = logging.Formatter("%(threadName)s : %(message)s")
syslog.setFormatter(formatter)
logger.setLevel(logging.INFO)
logger.addHandler(syslog)


def build_ceserver():
    """Clone cheat-engine and build ceserver for all architectures using NDK."""
    ndk_home = os.getenv("ANDROID_NDK_HOME") or os.getenv("NDK_HOME")
    if not ndk_home:
        raise RuntimeError(
            "ANDROID_NDK_HOME or NDK_HOME environment variable must be set"
        )

    ndk_build = Path(ndk_home) / "ndk-build"
    if not ndk_build.exists():
        raise RuntimeError(f"ndk-build not found at {ndk_build}")

    ce_dir = PATH_BASE / "cheat-engine"
    ce_build_dir = ce_dir / "Cheat Engine" / "ceserver" / "ndk-build" / "EXECUTABLE"

    if not ce_dir.exists():
        logger.info("Cloning cheat-engine repository...")
        subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "https://github.com/cheat-engine/cheat-engine.git",
                str(ce_dir),
            ],
            check=True,
        )
    else:
        logger.info("cheat-engine directory already exists, skipping clone")

    logger.info("Building ceserver with ndk-build...")
    subprocess.run(
        [str(ndk_build)],
        cwd=ce_build_dir,
        check=True,
    )

    logger.info("Copying built binaries to downloads/")
    PATH_DOWNLOADS.mkdir(parents=True, exist_ok=True)

    libs_dir = ce_build_dir / "libs"
    for ndk_arch, mod_arch in ARCH_MAP.items():
        src = libs_dir / ndk_arch / "ceserver"
        if not src.exists():
            raise FileNotFoundError(f"Expected built binary not found: {src}")
        dst = PATH_DOWNLOADS / f"ceserver-{mod_arch}"
        shutil.copy(src, dst)
        logger.info(f"Copied {ndk_arch} -> ceserver-{mod_arch}")


def generate_version_code(project_tag: str) -> int:
    parts = re.split("[-.]", project_tag)
    version_code = "".join(f"{int(part):02d}" for part in parts)
    return int(version_code)


def create_module_prop(path: Path, project_tag: str):
    module_prop = f"""id=magisk-ceserver
name=MagiskCEServer
version={project_tag}
versionCode={generate_version_code(project_tag)}
author=cloei
updateJson=https://github.com/cloei/magisk-frida/releases/latest/download/updater.json
description=Run ceserver on boot"""

    with open(path.joinpath("module.prop"), "w", newline="\n") as f:
        f.write(module_prop)


def create_module():
    logger.info("Creating module")

    if PATH_BUILD_TMP.exists():
        shutil.rmtree(PATH_BUILD_TMP)

    shutil.copytree(PATH_BASE_MODULE, PATH_BUILD_TMP)


def fill_module(arch: str):
    logger.info(f"Filling module for arch '{arch}'")

    src_path = PATH_DOWNLOADS / f"ceserver-{arch}"
    if not src_path.exists():
        raise FileNotFoundError(
            f"ceserver binary not found: {src_path}. "
            "Run build_ceserver() first or ensure binaries are in downloads/."
        )

    files_dir = PATH_BUILD_TMP / "files"
    files_dir.mkdir(exist_ok=True)
    shutil.copy(src_path, files_dir / f"ceserver-{arch}")


def create_updater_json(project_tag: str):
    logger.info("Creating updater.json")

    updater = {
        "version": project_tag,
        "versionCode": generate_version_code(project_tag),
        "zipUrl": f"https://github.com/cloei/magisk-frida/releases/download/{project_tag}/MagiskCEServer-{project_tag}.zip",
        "changelog": "https://github.com/cheat-engine/cheat-engine/releases",
    }

    with open(PATH_BUILD / "updater.json", "w", newline="\n") as f:
        f.write(json.dumps(updater, indent=4))


def package_module(project_tag: str):
    logger.info("Packaging module")

    module_zip = PATH_BUILD / f"MagiskCEServer-{project_tag}.zip"

    with zipfile.ZipFile(module_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(PATH_BUILD_TMP):
            for file_name in files:
                if file_name == "placeholder" or file_name == ".gitkeep":
                    continue
                zf.write(
                    Path(root) / file_name,
                    arcname=Path(root).relative_to(PATH_BUILD_TMP) / file_name,
                )

    shutil.rmtree(PATH_BUILD_TMP)


def do_build(project_tag: str):
    PATH_DOWNLOADS.mkdir(parents=True, exist_ok=True)
    PATH_BUILD.mkdir(parents=True, exist_ok=True)

    create_module()
    create_module_prop(PATH_BUILD_TMP, project_tag)

    for arch in ARCH_MAP.values():
        fill_module(arch)

    package_module(project_tag)
    create_updater_json(project_tag)

    logger.info("Done")
