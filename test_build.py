import pathlib
import tempfile
import unittest
from unittest.mock import patch
import build


class BuilderTests(unittest.TestCase):
    def test_suffix_group_roundtrip(self):
        data = build.blob(1, build.group('geo-block', ['example.com', 'example.org']))
        cats = build.categories(data)
        self.assertEqual(build.domains(cats['geo-block']), [(2, 'example.com'), (2, 'example.org')])

    def test_truncated_wire_rejected(self):
        for data in [b'\x0a\xff', b'\x0a\x05x', b'\x00', b'\x0d\x01']:
            with self.subTest(data=data), self.assertRaises(ValueError):
                list(build.fields(data))

    def test_previous_generation_survives_failure(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            old = root / 'release-old'
            old.mkdir()
            (old / 'geosite.dat').write_bytes(b'previous-known-good')
            (root / 'current').symlink_to(old.name)
            with patch.object(build, 'fetch', return_value=b'broken upstream'):
                with self.assertRaises((ValueError, KeyError, StopIteration, UnicodeError)):
                    build.build(root)
            self.assertEqual((root / 'current').readlink(), pathlib.Path('release-old'))
            self.assertEqual((root / 'current' / 'geosite.dat').read_bytes(), b'previous-known-good')
            self.assertEqual(list(root.glob('.build-*')), [])


if __name__ == '__main__':
    unittest.main()
