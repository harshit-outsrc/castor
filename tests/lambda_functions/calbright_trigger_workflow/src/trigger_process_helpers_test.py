import unittest
from propus.calbright_sql.user import User
from lambda_functions.calbright_trigger_workflow.src.trigger_process_helpers import (
    filter_check,
    format_edu_goal,
    format_ethnicity,
    format_gender,
    format_grade_level,
)


class TestTriggerProcessHelpers(unittest.TestCase):
    def setUp(self):
        self.student_data = {"ccc_id": "TEST123"}

    def test_filter_check(self):
        self.assertEqual(
            filter_check(User.ccc_id.key, self.student_data.get("ccc_id")),
            User.ccc_id.key == self.student_data.get("ccc_id"),
        )
        self.assertEqual(filter_check(User.ccc_id.key, None), None)

    def test_format_edu_goal(self):
        self.assertTrue(format_edu_goal("A"))
        self.assertTrue(format_edu_goal("B"))
        self.assertTrue(format_edu_goal("C"))
        self.assertTrue(format_edu_goal("D"))
        self.assertTrue(format_edu_goal("E"))
        self.assertTrue(format_edu_goal("F"))
        self.assertTrue(format_edu_goal("G"))
        self.assertTrue(format_edu_goal("H"))
        self.assertTrue(format_edu_goal("I"))
        self.assertTrue(format_edu_goal("J"))
        self.assertTrue(format_edu_goal("K"))
        self.assertTrue(format_edu_goal("L"))
        self.assertTrue(format_edu_goal("M"))
        self.assertTrue(format_edu_goal("N"))
        self.assertTrue(format_edu_goal("O"))
        self.assertFalse(format_edu_goal("a"))
        self.assertFalse(format_edu_goal("Z"))

    def test_format_gender(self):
        self.assertTrue(format_gender("F"))
        self.assertTrue(format_gender("M"))
        self.assertTrue(format_gender("B"))
        self.assertTrue(format_gender("X"))
        self.assertTrue(format_gender(None))
        self.assertFalse(format_gender("Z"))

    def test_format_ethnicity(self):
        self.assertFalse(format_ethnicity("XNNNNNNNNNNNNNNNNNNN"))
        self.assertFalse(format_ethnicity("NNNNNNNNNNNNNNNNNNNN"))
        self.assertTrue(format_ethnicity("YYYYYYYYYYYYYYYYYYYY"))
        self.assertFalse(format_ethnicity("ZZZZZZZZZZZZZZZZZZZZ"))

    def test_format_grade_level(self):
        self.assertEqual(format_grade_level("5"), 1)
        self.assertEqual(format_grade_level("Z"), 1)
        self.assertEqual(format_grade_level("X"), 2)
        self.assertEqual(format_grade_level("7"), 4)
        self.assertEqual(format_grade_level("8"), 7)


if __name__ == "__main__":
    unittest.main()
