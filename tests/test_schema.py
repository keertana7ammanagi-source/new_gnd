import unittest
from config.telemetry_schema import TELEMETRY_SCHEMA, EXPECTED_FIELD_COUNT, validate_schema

class TestSchema(unittest.TestCase):
    def test_schema_field_count(self):
        self.assertEqual(len(TELEMETRY_SCHEMA), EXPECTED_FIELD_COUNT)
        self.assertEqual(EXPECTED_FIELD_COUNT, 37)

    def test_schema_indices_are_sequential(self):
        for i, field in enumerate(TELEMETRY_SCHEMA):
            self.assertEqual(field.index, i)

    def test_schema_unique_names(self):
        names = [f.name for f in TELEMETRY_SCHEMA]
        self.assertEqual(len(names), len(set(names)))

    def test_no_mechanical_gyro(self):
        names = [f.name for f in TELEMETRY_SCHEMA]
        self.assertNotIn("MECHANICAL_GYRO", names)
        self.assertNotIn("GYRO_SPIN_RATE", names)

    def test_validate_schema_passes_on_valid_schema(self):
        # Should not raise any exception
        validate_schema()

if __name__ == '__main__':
    unittest.main()
