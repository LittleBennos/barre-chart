"""Run from the repo root: python -m unittest discover -s scripts"""
import unittest

from build_data import children_by_sa2, children_per_studio, leaked_names

# Shape copied from a real ABS ERP_ASGS2021 response (Footscray, 2025).
ERP_CSV = """DATAFLOW,MEASURE,SEX,AGE,REGION_TYPE,ASGS_2021,FREQ,TIME_PERIOD,OBS_VALUE,UNIT_MEASURE,OBS_STATUS,OBS_COMMENT
ABS:ERP_ASGS2021(1.0.0),ERP,3,A59,SA2,213031348,A,2025,561,PSNS,,
ABS:ERP_ASGS2021(1.0.0),ERP,3,A10,SA2,213031348,A,2025,568,PSNS,,
"""


class BuildDataTest(unittest.TestCase):
    def test_children_adds_both_age_groups(self):
        self.assertEqual(children_by_sa2(ERP_CSV, ["213031348"])["213031348"], 1129)

    def test_area_missing_from_abs_response_is_an_error(self):
        with self.assertRaises(ValueError):
            children_by_sa2(ERP_CSV, ["213031348", "213031349"])

    def test_children_per_studio(self):
        self.assertEqual(children_per_studio(1129, 3), 376)
        self.assertIsNone(children_per_studio(1129, 0))

    def test_studio_names_never_reach_published_text(self):
        published = '{"sa2_name":"Footscray","studios":2}'
        # A made-up studio name: real ones never go in the repo.
        self.assertEqual(leaked_names(published, ["Example Dance Academy"]), [])
        self.assertEqual(leaked_names('{"note":"EXAMPLE DANCE ACADEMY"}', ["Example Dance Academy"]), ["Example Dance Academy"])


if __name__ == "__main__":
    unittest.main()
