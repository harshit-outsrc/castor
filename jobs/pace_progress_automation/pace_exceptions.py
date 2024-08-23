class MissingRequiredHeader(Exception):
    def __init__(self, header):
        super().__init__(f"{header} is not in the google sheets header and execution has stopped")


class GSheetIncorrectTabName(Exception):
    def __init__(self, worksheet_title):
        super().__init__(f"Worksheet Retrieved ({worksheet_title}) does not match expected. Quitting")
