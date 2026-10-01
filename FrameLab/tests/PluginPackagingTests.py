import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "UnrealIntegration/install_plugin.py"
SPEC = importlib.util.spec_from_file_location("install_plugin", SCRIPT)
INSTALLER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INSTALLER)


class PackagingTests(unittest.TestCase):
    def test_package_and_preserve_existing_project(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "Demo.uproject"
            original = '{"FileVersion": 3}'
            project.write_text(original)
            installed = INSTALLER.install(project)
            self.assertEqual(project.read_text(), original)
            descriptor = json.loads((installed / "FrameLabPhysics.uplugin").read_text())
            self.assertEqual(descriptor["Modules"][0]["Name"], "FrameLabPhysics")
            private = installed / "Source/FrameLabPhysics/Private"
            self.assertFalse(list((private / "PhysicsCore").rglob("*.cpp")))
            for name in ("ClassicalEtherModel", "SpecialRelativityModel", "MichelsonMorleyExperiment"):
                self.assertTrue((private / f"PhysicsCore/src/{name}.inl").is_file())
                original_source = SCRIPT.parent.parent / f"PhysicsCore/src/{name}.cpp"
                self.assertEqual((private / f"PhysicsCore/src/{name}.inl").read_bytes(),
                                 original_source.read_bytes())
            for wrapper in private.glob("*Core.cpp"):
                self.assertIn('.inl"', wrapper.read_text())
            self.assertTrue((private / "PhysicsCore/include/FrameLab/InterferometerInput.h").is_file())
            with self.assertRaises(FileExistsError):
                INSTALLER.install(project)
            self.assertTrue((installed / "FrameLabPhysics.uplugin").is_file())

    def test_invalid_project(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                INSTALLER.install(Path(temp) / "Missing.uproject")
            malformed = Path(temp) / "Bad.uproject"
            malformed.write_text("invalid json")
            with self.assertRaises(ValueError):
                INSTALLER.install(malformed)
            self.assertFalse((Path(temp) / "Plugins").exists())


if __name__ == "__main__":
    unittest.main()
