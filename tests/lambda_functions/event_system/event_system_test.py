import unittest
from unittest.mock import MagicMock, Mock

from event_system import EventSystem
from exceptions import UnknownEventType, EmptyEventData


class TestEventSystem(unittest.TestCase):
    def setUp(self) -> None:
        self.configs = "my_super_special_configs"
        self.ssm = "my_ssm_service"
        self.event_data = {"run": "to_the_right"}
        self.build_called = self.run_called = False

    def test_required_attributes(self):
        configs = "a.b.c.d.e"
        ssm = "aws_ssm_class"
        es = EventSystem(configs, "csep_complete", ssm, None)
        for value in es._event_type_mapping.values():
            self.assertTrue(hasattr(value, "run"))
            self.assertTrue(hasattr(value, "build"))
        self.assertEqual(es.configs, configs)
        self.assertEqual(es.ssm, ssm)

    def test_event_error(self):
        with self.assertRaises(UnknownEventType):
            EventSystem(None, "bad_event_type", None, None)

        with self.assertRaises(EmptyEventData):
            es = EventSystem(None, "csep_complete", None, None)
            es.process_event({"event_type": "csep_complete"})

    def test_process_event(self):
        es = EventSystem(self.configs, "csep_complete", self.ssm, None)
        mock_csep_complete = MagicMock()
        mock_csep_complete.build = Mock(side_effect=self.mock_build)
        es._event_type_mapping["csep_complete"] = mock_csep_complete

        es.process_event({"event_type": "csep_complete", "event_data": self.event_data})
        self.assertTrue(self.build_called and self.run_called)

    def mock_build(self, configs, ssm):
        self.build_called = True
        self.assertTrue(configs == self.configs and ssm == self.ssm)
        mock_csep_complete = MagicMock()
        mock_csep_complete.run = Mock(side_effect=self.mock_run)
        return mock_csep_complete

    def mock_run(self, event_data):
        self.assertEqual(event_data, self.event_data)
        self.run_called = True

        error_received = False
        try:
            es = EventSystem(None, "csep_complete", None, None)
            es.process_event({"event_type": "csep_complete"})
        except EmptyEventData as err:
            error_received = True
            self.assertEqual(str(err), 'Event type "csep_complete" was sent with no data')
        self.assertTrue(error_received)


if __name__ == "__main__":
    unittest.main()
