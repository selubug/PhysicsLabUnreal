#!/usr/bin/env python3
"""Package the runtime plugin and the current shared core into a UE project."""
import argparse
import json
from pathlib import Path
import shutil
import tempfile


def install(project_file: Path) -> Path:
    project_file = project_file.expanduser().resolve()
    if not project_file.is_file() or project_file.suffix != ".uproject":
        raise ValueError("Pass an existing .uproject file.")
    json.loads(project_file.read_text(encoding="utf-8-sig"))
    source = Path(__file__).resolve().parent
    plugins = project_file.parent / "Plugins"
    plugins.mkdir(exist_ok=True)
    destination = plugins / "FrameLabPhysics"
    if destination.exists():
        raise FileExistsError(
            f"{destination} already exists. Back it up and remove it before reinstalling.")
    # Stage the full package first; a failed copy does not leave a partial plugin.
    with tempfile.TemporaryDirectory(prefix="framelab-", dir=plugins) as temporary:
        staged = Path(temporary) / "FrameLabPhysics"
        shutil.copytree(source / "FrameLabPhysics", staged)
        shutil.copytree(source.parent / "PhysicsCore",
                        staged / "Source/FrameLabPhysics/Private/PhysicsCore")
        # UBT recursively discovers .cpp files. Wrappers above compile the core;
        # rename the packaged originals so UBT cannot compile them a second time.
        for cpp in (staged / "Source/FrameLabPhysics/Private/PhysicsCore/src").glob("*.cpp"):
            cpp.rename(cpp.with_suffix(".inl"))
        for wrapper in (staged / "Source/FrameLabPhysics/Private").glob("*Core.cpp"):
            wrapper.write_text(wrapper.read_text().replace('.cpp"', '.inl"'))
        staged.rename(destination)
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="Path to an existing Unreal .uproject")
    args = parser.parse_args()
    try:
        print(f"Installed {install(args.project)}")
    except (OSError, ValueError) as error:
        parser.exit(1, f"Installation failed: {error}\n")
