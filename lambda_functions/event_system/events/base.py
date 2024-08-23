from typing import AnyStr, Dict
from collections.abc import Iterable
from propus.aws.ssm import AWS_SSM
from propus.logging_utility import Logging
from exceptions import MissingRequiredField, UnhandledEventData


class BaseEventSystem:
    __event_type__ = "base_event"

    def __init__(self, configs={}, ssm=AWS_SSM.build()):
        self.logger = Logging.get_logger("event/base_event")
        _constants = configs.get("constants")
        if _constants and isinstance(_constants, str):
            self.constants = ssm.get_param(_constants, param_type="json")
        elif _constants and isinstance(_constants, dict):
            self.constants = _constants
        else:
            self.constants = {}

        _feature_flags = configs.get("feature_flags")
        if _feature_flags and isinstance(_feature_flags, str):
            ssm_features = ssm.get_param(_feature_flags, param_type="json")
        elif _feature_flags and isinstance(_feature_flags, dict):
            ssm_features = _feature_flags
        else:
            ssm_features = {}
        feature_flags = ssm_features.get("castor", {}).get(self.__event_type__, {})
        if feature_flags.get("active", False):
            self.features_enabled = feature_flags.get("enabled")
        else:
            self.features_enabled = []

    @staticmethod
    def check_required_fields(event_type: AnyStr, event: Dict, required_fields: set):
        for field in required_fields:
            if len(event.get(field, "")) == 0:
                raise MissingRequiredField(event_type, field)

    @staticmethod
    def yield_bulk_data(event_type, event):
        """
        yield_bulk_data takes in event data as either a single event or as an iterable
        of events and yields the event(s) for processing.


        Arguments:
            event_type (str): Name of the event type
            event (dict or iterable): Event(s) to be processed

        Returns:
            generator of the event(s) to be processed

        Raises:
            UnhandledEventData: if event is not a dict or an interable
        """
        if isinstance(event, dict):
            yield event
        elif isinstance(event, Iterable):
            for e in event:
                yield e
        else:
            raise UnhandledEventData(event_type)


def is_feature_enabled(func):
    def wrapper(self, *args, **kwargs):
        if self.features_enabled and ("ALL" in self.features_enabled or func.__name__ in self.features_enabled):
            return func(self, *args, **kwargs)
        self.logger.info(f"Event {self.__event_type__} feature is disabled: {func.__name__}")

    return wrapper
