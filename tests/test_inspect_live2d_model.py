import json
import tempfile
import unittest
from pathlib import Path

from scripts.inspect_live2d_model import _format_text, inspect_model


class InspectLive2DModelTests(unittest.TestCase):
    def test_reports_missing_core_expression_and_motion_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            model_dir = Path(temp_dir) / "sample" / "runtime"
            model_dir.mkdir(parents=True)
            (model_dir / "sample.moc3").write_bytes(b"moc")
            (model_dir / "textures").mkdir()
            (model_dir / "textures" / "texture_00.png").write_bytes(b"png")

            model_path = model_dir / "sample.model3.json"
            model_path.write_text(
                json.dumps(
                    {
                        "Version": 3,
                        "FileReferences": {
                            "Moc": "sample.moc3",
                            "Textures": [
                                "textures\\texture_00.png",
                                "textures/texture_01.png",
                            ],
                            "Physics": "sample.physics3.json",
                            "Expressions": [
                                {"Name": "smile", "File": "smile.exp3.json"}
                            ],
                            "Motions": {"Idle": [{"File": "idle.motion3.json"}]},
                        },
                    }
                ),
                encoding="utf-8",
            )

            summary = inspect_model(
                model_path,
                Path(temp_dir),
                model_name=None,
                character_name=None,
            )

            self.assertEqual(summary["texture_count"], 2)
            self.assertEqual(len(summary["core_files"]), 4)
            core_status = {
                entry["file"]: entry["exists"] for entry in summary["core_files"]
            }
            self.assertTrue(core_status["sample.moc3"])
            self.assertTrue(core_status["textures\\texture_00.png"])
            self.assertEqual(
                {entry["kind"] for entry in summary["missing_files"]},
                {"texture", "physics", "expression", "motion"},
            )
            report = _format_text(summary)
            self.assertIn("## Missing referenced files", report)
            self.assertIn("sample.physics3.json", report)
            self.assertIn("idle.motion3.json", report)

    def test_ignores_invalid_texture_container_instead_of_counting_characters(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = Path(temp_dir) / "sample.model3.json"
            model_path.write_text(
                json.dumps({"FileReferences": {"Textures": "not-a-list"}}),
                encoding="utf-8",
            )

            summary = inspect_model(
                model_path,
                Path(temp_dir),
                model_name=None,
                character_name=None,
            )

            self.assertEqual(summary["texture_count"], 0)
            self.assertEqual(summary["core_files"], [])
            self.assertEqual(summary["missing_files"], [])


if __name__ == "__main__":
    unittest.main()
