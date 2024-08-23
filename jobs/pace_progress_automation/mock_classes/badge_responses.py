"""
This file is only used for test driven development. Since Pace/Progress is tied to a student's progress and
create mock data in Salesforce for badges is cumbersome we can use these functions to mock the response from
Salesforce.
"""
from datetime import datetime, timedelta


from const.crm_badge_progress_constants import (
    crm_timeline_60_day,
    crm_timeline_90_day,
    crm_timeline_120_day,
    crm_timeline_180_day,
    crm_timeline_365_day,
)

BADGE_MAP = {
    "60 Day": crm_timeline_60_day,
    "90 Day": crm_timeline_90_day,
    "120 Day": crm_timeline_120_day,
    "180 Day": crm_timeline_180_day,
    "365 Day": crm_timeline_365_day,
}


def fetch_ontrack_badges(timeline, week_number):
    weekly_badges = BADGE_MAP.get(timeline)
    all_badges_completed = [
        weekly_badges.get(f"week{idx+1}") for idx in range(week_number) if weekly_badges.get(f"week{idx+1}")
    ]
    return fetch_badge_response(all_badges_completed)


def fetch_behind_badges(timeline, week_number):
    weekly_badges = BADGE_MAP.get(timeline)
    all_badges_completed = []
    for idx in range(week_number):
        if weekly_badges.get(f"week{idx+1}"):
            all_badges_completed += [
                weekly_badges.get(f"week{idx+1}")[b] for b in range(0, len(weekly_badges.get(f"week{idx+1}")), 2)
            ]
    return fetch_badge_response(all_badges_completed)


def fetch_ahead_badges(timeline, week_number, cond="some"):
    weekly_badges = BADGE_MAP.get(timeline)
    all_badges_completed = []
    for idx in range(week_number):
        if weekly_badges.get(f"week{idx+1}"):
            all_badges_completed += weekly_badges.get(f"week{idx+1}")

    next_week_found = False
    while not next_week_found:
        idx += 1
        if weekly_badges.get(f"week{idx+1}"):
            if cond == "some":
                all_badges_completed += weekly_badges.get(f"week{idx+1}")[:2]
            else:
                all_badges_completed += weekly_badges.get(f"week{idx+1}")
            next_week_found = True
    return fetch_badge_response(all_badges_completed)


def fetch_badge_response(all_badges_completed):
    records = []
    for idx, badge in enumerate(all_badges_completed):
        records.append(
            {
                "trailheadapp__Badge__r": {"Name": badge},
                "CreatedDate": (datetime.now() - timedelta(days=idx + 1)).strftime("%Y-%m-%dT%H:%M:%S.000+0000"),
            }
        )
    return {"totalSize": len(records), "records": records}
