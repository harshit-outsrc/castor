from propus.calbright_sql.calbright import Calbright
from propus.canvas import Canvas
from propus.salesforce import Salesforce
from events.base_event import BaseEvent


class AssetAccessedEvent(BaseEvent):
    """
    This class is used to process the Asset Accessed Event
    https://canvas.instructure.com/doc/api/file.data_service_canvas_asset.html
    """

    def __init__(self, event, psql_engine: Calbright, sf_client: Salesforce, canvas_client: Canvas):
        super().__init__(event, psql_engine, sf_client, canvas_client)

    def process(self):
        self.process_non_saa_activity_event(activity_type="asset")
        return True
