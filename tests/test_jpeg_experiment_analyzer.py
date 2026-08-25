import base64
import importlib.util
from pathlib import Path
import tempfile
import unittest


JPEG_A = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAAGAAgDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwDi6KKK+ZP3E//Z"
)

JPEG_B = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAAGAAgDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwDWooor80PyA//Z"
)


def load_analyzer():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "analyze_jpeg_experiment.py"
    spec = importlib.util.spec_from_file_location("pc3_jpeg_analyzer", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class JpegExperimentAnalyzerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analyzer = load_analyzer()

    def test_parses_baseline_jpeg_structure_without_optional_dependencies(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "a.jpg"
            path.write_bytes(JPEG_A)
            result = self.analyzer.parse_jpeg(path)

        self.assertTrue(result["valid_soi"])
        self.assertTrue(result["valid_eoi"])
        self.assertIsNotNone(result["frame"])
        self.assertEqual(result["frame"]["kind"], "SOF0_baseline_dct")
        self.assertEqual(result["frame"]["width"], 8)
        self.assertEqual(result["frame"]["height"], 6)
        self.assertEqual(len(result["frame"]["components"]), 3)
        self.assertGreaterEqual(len(result["quantization_tables"]), 2)
        self.assertGreaterEqual(len(result["huffman_tables"]), 1)
        self.assertEqual(result["scan_count"], 1)
        self.assertFalse(result["is_progressive"])

    def test_different_pixel_content_can_share_encoder_structure(self):
        with tempfile.TemporaryDirectory() as temp:
            a = Path(temp) / "a.jpg"
            b = Path(temp) / "b.jpg"
            a.write_bytes(JPEG_A)
            b.write_bytes(JPEG_B)
            ja = self.analyzer.parse_jpeg(a)
            jb = self.analyzer.parse_jpeg(b)

        self.assertNotEqual(self.analyzer.sha256_bytes(JPEG_A), self.analyzer.sha256_bytes(JPEG_B))
        self.assertEqual(ja["frame"], jb["frame"])
        self.assertEqual(ja["quantization_tables"], jb["quantization_tables"])
        self.assertEqual(ja["huffman_tables"], jb["huffman_tables"])

    def test_file_record_binds_hash_size_and_jpeg_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "a.jpg"
            path.write_bytes(JPEG_A)
            record = self.analyzer.file_record(path)

        self.assertEqual(record["bytes"], len(JPEG_A))
        self.assertEqual(record["sha256"], "f12df05bb5d3054053efed619d57c2eebcd5d0640760b14518d4e8f08a172e68")
        self.assertTrue(record["jpeg"]["valid_soi"])


if __name__ == "__main__":
    unittest.main()
