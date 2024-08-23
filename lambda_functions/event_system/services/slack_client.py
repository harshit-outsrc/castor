from services.base_client import fetch_ssm

CHANNEL_ID_TABLE = {
    "enrollment-agreement": "GPN1Q0E11",
    "log-career-readiness-automations": "C030B9YDB9C",
    "log-data-analysis-automations": "C03J3JYS28K",
    "log-dei-automations": "C02EZ613138",
    "new-learner-device-log": "C02L8MF42V8",
    "new-learner-device-log-admin": "C02M371U4M6",
    "log-crmadmin-automations": "C01QT90LUSJ",
    "automations-test": "C02J24ZQSRX",
}


class SlackClient:
    _client = None

    def __new__(cls, param_name, ssm):
        if cls._client is None:
            from propus.slack import Slack

            param = fetch_ssm(ssm, param_name, is_json=True)

            cls._client = Slack.build(param)
        return cls._client


class SlackService:
    def __init__(self, param_name, ssm):
        self.client = SlackClient(param_name, ssm)

    def alert_student_signed_csep(self, channel, info):
        channel_id = CHANNEL_ID_TABLE.get(channel)
        message = (
            f"<https://calbright.lightning.force.com/lightning/r/Contact/{info.get('id')}/view|:salesforce:>"
            f" {info.get('name')} ({info.get('ccc_id')}) signed their CSEP for {info.get('intended_program')}"
            "and has been enrolled in the latest pathway competencies."
        )
        self.client.send_message(channel_id, message)

    def alert_admins_of_new_device_requested(self, channel, info):
        channel_id = CHANNEL_ID_TABLE.get(channel)
        message = (
            "I just added the following row to the <https://docs.google.com/spreadsheets/d/1SvdDhS_N63ZFfm91Dipgfi-UUyVw1MX2N0q_8gs6OxA/edit#gid=427006451|Blackdog device spreadsheet>\n"  # noqa E501
            f"\nStudent Name: {info.get('first_name')} {info.get('last_name')}"
            f"\nCCCID: <https://calbright.lightning.force.com/lightning/r/Contact/{info.get('id')}/view|{info.get('ccc_id')}>"  # noqa: E501
            f"\nInclude Chromebook: {info.get('cb_requested')}"
            f"\nInclude Hotspot: {info.get('hs_requested')}"
            f"\nShipping Address: {info.get('address')}"
            f"\nPolicy Signed: {info.get('policy_signed')}"
        )

        self.client.send_message(
            channel_id,
            message,
        )

    def alert_staff_of_device_added_to_gsheets_for_processing(self, channel, info):
        channel_id = CHANNEL_ID_TABLE.get(channel)
        message = (
            "User signed CSEP where they requested their new learner device. This new learner device request for "
            f"{info.get('first_name')} {info.get('last_name')} (CCC ID: {info.get('ccc_id')}) has been added. Within 48 hours, the device will be " # noqa E501
            "processed and a tracking number will be available."
        )
        self.client.send_message(
            channel_id,
            message,
        )

    def alert_staff_of_shipping_address_failure(self, channel, info):
        channel_id = CHANNEL_ID_TABLE.get(channel)
        message = (
            f"@es-team Failed on Post-CSEP Device Request for {info.get('first_name')} {info.get('last_name')} "
            f"(CCC ID: <https://calbright.lightning.force.com/lightning/r/Contact/{info.get('id')}/view|{info.get('ccc_id')}>)."  # noqa E501
            f"\nAddress Verification Status: {info.get('address_verification_status')}."
            "\nPlease verify shipping address and resubmit device request form for this student"
        )
        self.client.send_message(
            channel_id,
            message,
        )

    def alert_admins_of_tangoe_device_requested(self, channel, info):
        channel_id = CHANNEL_ID_TABLE.get(channel)
        message = (
            "I just added the following row to the <https://docs.google.com/spreadsheets/d/1yzdGpTiS0MdDAU6W_yvb4JHBzAhnH7KS8y9x5vfFKZU/edit?gid=1257732891#gid=1257732891>\n"  # noqa E501
            f"\nStudent Name: {info.get('first_name')} {info.get('last_name')}"
            f"\nCCCID: <https://calbright.lightning.force.com/lightning/r/Contact/{info.get('id')}/view|{info.get('ccc_id')}>"  # noqa: E501
            f"\nInclude Chromebook: {info.get('cb_requested')}"
            f"\nInclude Hotspot: {info.get('hs_requested')}"
            f"\nShipping Address: {info.get('address')}"
            f"\nPolicy Signed: {info.get('policy_signed')}"
        )

        self.client.send_message(
            channel_id,
            message,
        )

    def alert_staff_of_tangoe_duplicate_request(self, channel, info):
        channel_id = CHANNEL_ID_TABLE.get(channel)
        message = (
            "Duplicate device request detected for the following student and request NOT submitted to Tangoe\n"
            f"\nStudent Name: {info.get('first_name')} {info.get('last_name')}"
            f"\nCCCID: <https://calbright.lightning.force.com/lightning/r/Contact/{info.get('id')}/view|{info.get('ccc_id')}>"  # noqa: E501
        )

        self.client.send_message(
            channel_id,
            message,
        )

    def alert_admins_of_device_return(self, channel, info):
        channel_id = CHANNEL_ID_TABLE.get(channel)
        message = (
            "I just added the following row to the <https://docs.google.com/spreadsheets/d/1OW88PiqDUbVLnM-K9DPLHKEXOnwOy4awFVgk3F6wnsg/edit?gid=1425628734#gid=1425628734>\n"  # noqa E501
            f"\nStudent Name: {info.get('first_name')} {info.get('last_name')}"
            f"\nCCCID: <https://calbright.lightning.force.com/lightning/r/Contact/{info.get('id')}/view|{info.get('ccc_id')}>"  # noqa: E501
            f"\nReturn Chromebook: {info.get('cb_return')}"
            f"\nReturn Hotspot: {info.get('hs_return')}"
            f"\nShipping Address: {info.get('address')}"
            f"\nPolicy Signed: {info.get('policy_signed')}"
        )

        self.client.send_message(
            channel_id,
            message,
        )

    def alert_admins_of_device_replacement(self, channel, info):
        channel_id = CHANNEL_ID_TABLE.get(channel)
        message = (
            "I just added the following row to the <https://docs.google.com/spreadsheets/d/1OW88PiqDUbVLnM-K9DPLHKEXOnwOy4awFVgk3F6wnsg/edit?gid=2065647808#gid=2065647808>\n"  # noqa E501
            f"\nStudent Name: {info.get('first_name')} {info.get('last_name')}"
            f"\nCCCID: <https://calbright.lightning.force.com/lightning/r/Contact/{info.get('id')}/view|{info.get('ccc_id')}>"  # noqa: E501
            f"\nReplace Chromebook: {info.get('cb_replace')}"
            f"\nReplace Hotspot: {info.get('hs_replace')}"
            f"\nShipping Address: {info.get('address')}"
            f"\nPolicy Signed: {info.get('policy_signed')}"
        )

        self.client.send_message(
            channel_id,
            message,
        )

    def alert_admins_of_device_stolen(self, channel, info):
        channel_id = CHANNEL_ID_TABLE.get(channel)
        message = (
            "I just added the following row to the <https://docs.google.com/spreadsheets/d/1OW88PiqDUbVLnM-K9DPLHKEXOnwOy4awFVgk3F6wnsg/edit?gid=1287980932#gid=1287980932>\n"  # noqa E501
            f"\nStudent Name: {info.get('first_name')} {info.get('last_name')}"
            f"\nCCCID: <https://calbright.lightning.force.com/lightning/r/Contact/{info.get('id')}/view|{info.get('ccc_id')}>"  # noqa: E501
            f"\nChromebook Stolen: {info.get('cb_stolen')}"
            f"\nHotspot Stolen: {info.get('hs_stolen')}"
            f"\nShipping Address: {info.get('address')}"
            f"\nPolicy Signed: {info.get('policy_signed')}"
        )
        self.client.send_message(
            channel_id,
            message,
        )

    def alert_staff_of_duplicate_equipment_request(self, channel, info):
        channel_id = CHANNEL_ID_TABLE.get(channel)
        message = (
            f"@es-team Duplicate Device Request for {info.get('first_name')} {info.get('last_name')} "
            f"(CCC ID: <https://calbright.lightning.force.com/lightning/r/Contact/{info.get('id')}/view|{info.get('ccc_id')}>)."  # noqa E501
            f"\nStudent Attempted Duplicate Device Request"
        )
        self.client.send_message(
            channel_id,
            message,
        )
