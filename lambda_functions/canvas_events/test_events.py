test_events = {
    "asset_accessed": {
        "metadata": {
            "context_type": "Account",
            "context_id": "263480000000000001",
            "context_account_id": "263480000000000001",
            "context_sis_source_id": None,
            "root_account_uuid": "Ek0vx769rEFEnTt5SqzuGQAoktvvX6K6zfxJiNUH",
            "root_account_id": "263480000000000001",
            "root_account_lti_guid": "Hl5YGmLrMP9CBSgBxdT7OUSKiSDtfxOo6lZqacfh",
            "user_login": "brian.delizza@calbright.org",
            "user_account_id": "263480000000000001",
            "user_sis_id": "a1",
            "user_id": "263480000000000104",
            "time_zone": "America/Los_Angeles",
            "context_role": "AccountAdmin",
            "request_id": "e3a3981a-8f49-4aff-b63f-c98744c07a99",
            "session_id": "4187f46f2044e71e75935eca9016e2d8",
            "hostname": "calbright-dev.instructure.com",
            "http_method": "GET",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36",
            "client_ip": "47.157.76.180",
            "url": "https://calbright-dev.instructure.com/accounts/1/external_tools/106",
            "referrer": "https://calbright-dev.instructure.com/accounts/1?",
            "producer": "canvas",
            "event_name": "asset_accessed",
            "event_time": "2024-03-27T21:28:56.197Z",
        },
        "body": {
            "asset_name": "Canvas Data Services",
            "asset_type": "context_external_tool",
            "asset_id": "263480000000000106",
            "category": "external_tools",
            "role": "AccountUser",
            "url": "https://live-events-lti-iad-prod.inscloudgate.net/resource_link_request",
        },
    },
    "discussion_entry_created": {
        "metadata": {
            "context_type": "Course",
            "context_id": "263480000000000115",
            "context_account_id": "263480000000000001",
            "context_sis_source_id": None,
            "root_account_uuid": "Ek0vx769rEFEnTt5SqzuGQAoktvvX6K6zfxJiNUH",
            "root_account_id": "263480000000000001",
            "root_account_lti_guid": "Hl5YGmLrMP9CBSgBxdT7OUSKiSDtfxOo6lZqacfh",
            "user_login": "tony.pizza@calbright.org",
            "user_account_id": "263480000000000001",
            "user_sis_id": "a1",
            "user_id": "263480000000000134",
            "time_zone": "America/Los_Angeles",
            "real_user_id": "263480000000000104",
            "context_role": "StudentEnrollment",
            "request_id": "0f1c22d4-0727-4c33-ba03-4ccae00577be",
            "session_id": "1b9c812ea0278d4b03913f4ad428e1b4",
            "hostname": "calbright-dev.instructure.com",
            "http_method": "POST",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36",
            "client_ip": "104.172.197.20",
            "url": "https://calbright-dev.instructure.com/api/v1/courses/115/discussion_topics/118/entries",
            "referrer": "https://calbright-dev.instructure.com/courses/115/discussion_topics/118",
            "producer": "canvas",
            "event_name": "discussion_entry_created",
            "event_time": "2024-06-29T02:36:16.873Z",
        },
        "body": {
            "user_id": "134",
            "created_at": "2024-06-28T19:36:16-07:00",
            "discussion_entry_id": "7",
            "discussion_topic_id": "118",
            "text": "<p>Hello it's me</p>",
        },
    },
    "discussion_entry_submitted": {
        "metadata": {
            "context_type": "Course",
            "context_id": "263480000000000115",
            "context_account_id": "263480000000000001",
            "context_sis_source_id": None,
            "root_account_uuid": "Ek0vx769rEFEnTt5SqzuGQAoktvvX6K6zfxJiNUH",
            "root_account_id": "263480000000000001",
            "root_account_lti_guid": "Hl5YGmLrMP9CBSgBxdT7OUSKiSDtfxOo6lZqacfh",
            "user_login": "jimmy.pasta.test@calbright.org",
            "user_account_id": "263480000000000001",
            "user_sis_id": "pasta1",
            "user_id": "263480000000000141",
            "time_zone": "America/Los_Angeles",
            "real_user_id": "263480000000000104",
            "context_role": "StudentEnrollment",
            "request_id": "2df184c9-01c1-4810-9d1a-cc4fef84a98b",
            "session_id": "5f30a8a1ec5829125eef24653bbe28e0",
            "hostname": "calbright-dev.instructure.com",
            "http_method": "POST",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36",
            "client_ip": "104.172.197.20",
            "url": "https://calbright-dev.instructure.com/api/v1/courses/115/discussion_topics/118/entries",
            "referrer": ("https://calbright-dev.instructure.com/courses/115/discussion_topics/118?module_item_id=620"),
            "producer": "canvas",
            "event_name": "discussion_entry_submitted",
            "event_time": "2024-07-09T03:37:46.795Z",
        },
        "body": {
            "user_id": "141",
            "created_at": "2024-07-08T20:37:46-07:00",
            "discussion_entry_id": "21",
            "discussion_topic_id": "118",
            "text": "<p>wow</p>",
        },
    },
    "discussion_topic_created": {
        "metadata": {
            "context_type": "Course",
            "context_id": "263480000000000106",
            "context_account_id": "263480000000000001",
            "context_sis_source_id": "TEST-102-UPDATED",
            "root_account_uuid": "Ek0vx769rEFEnTt5SqzuGQAoktvvX6K6zfxJiNUH",
            "root_account_id": "263480000000000001",
            "root_account_lti_guid": "Hl5YGmLrMP9CBSgBxdT7OUSKiSDtfxOo6lZqacfh",
            "user_login": "testeroni12357465asd7@calbright.org",
            "user_account_id": "263480000000000001",
            "user_sis_id": "a1",
            "user_id": "263480000000000109",
            "time_zone": "America/Los_Angeles",
            "real_user_id": "263480000000000104",
            "context_role": "StudentEnrollment",
            "request_id": "d5ffc838-d6a7-4561-bb51-64fa9962a707",
            "session_id": "4187f46f2044e71e75935eca9016e2d8",
            "hostname": "calbright-dev.instructure.com",
            "http_method": "POST",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"
            " Chrome/123.0.0.0 Safari/537.36",
            "client_ip": "47.157.76.180",
            "url": "https://calbright-dev.instructure.com/api/v1/courses/106/discussion_topics",
            "referrer": "https://calbright-dev.instructure.com/courses/106/discussion_topics/new",
            "producer": "canvas",
            "event_name": "discussion_topic_created",
            "event_time": "2024-03-29T22:43:00.351Z",
        },
        "body": {
            "discussion_topic_id": "263480000000000108",
            "is_announcement": False,
            "title": "Why Are Girl Scout Cookies Seasonal?",
            "body": "<p>In this discussion post I will explore the effects of the seasonal nature on cookie "
            "purchasers. Thanks for coming to my TED talk.</p>",
            "context_id": "106",
            "context_type": "Course",
            "workflow_state": "active",
            "updated_at": "2024-03-29T15:43:00-07:00",
        },
    },
    "discussion_topic_updated": {
        "metadata": {
            "context_type": "Course",
            "context_id": "263480000000000106",
            "context_account_id": "263480000000000001",
            "context_sis_source_id": "TEST-102-UPDATED",
            "root_account_uuid": "Ek0vx769rEFEnTt5SqzuGQAoktvvX6K6zfxJiNUH",
            "root_account_id": "263480000000000001",
            "root_account_lti_guid": "Hl5YGmLrMP9CBSgBxdT7OUSKiSDtfxOo6lZqacfh",
            "user_login": "testeroni12357465asd7@calbright.org",
            "user_account_id": "263480000000000001",
            "user_sis_id": "a1",
            "user_id": "263480000000000109",
            "time_zone": "America/Los_Angeles",
            "real_user_id": "263480000000000104",
            "context_role": "StudentEnrollment",
            "request_id": "e51b4951-946b-410b-93b9-30521bd47980",
            "session_id": "4187f46f2044e71e75935eca9016e2d8",
            "hostname": "calbright-dev.instructure.com",
            "http_method": "PUT",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36",
            "client_ip": "47.157.76.180",
            "url": "https://calbright-dev.instructure.com/api/v1/courses/106/discussion_topics/108",
            "referrer": "https://calbright-dev.instructure.com/courses/106/discussion_topics/108/edit",
            "producer": "canvas",
            "event_name": "discussion_topic_updated",
            "event_time": "2024-03-29T23:00:06.219Z",
        },
        "body": {
            "discussion_topic_id": "263480000000000108",
            "is_announcement": False,
            "title": "Why Are Girl Scout Cookies Seasonal?",
            "body": "<p>In this discussion post I will explore the effects of the seasonal nature on cookie"
            " purchasers. Thanks for coming to my TED talk.</p><p>I am updating this to include that"
            " Thin Mints are the best girl scout cookie.</p>",
            "context_id": "106",
            "context_type": "Course",
            "workflow_state": "active",
            "updated_at": "2024-03-29T16:00:06-07:00",
        },
    },
    "submission_created": {
        "metadata": {
            "root_account_uuid": "Ek0vx769rEFEnTt5SqzuGQAoktvvX6K6zfxJiNUH",
            "root_account_id": "263480000000000001",
            "root_account_lti_guid": "Hl5YGmLrMP9CBSgBxdT7OUSKiSDtfxOo6lZqacfh",
            "request_id": "4849f03d-459f-4de9-a690-381ed92a338c",
            "session_id": None,
            "hostname": "calbright-dev.instructure.com",
            "http_method": "POST",
            "user_agent": "GuzzleHttp/7",
            "client_ip": "35.168.19.245",
            "url": "https://calbright-dev.instructure.com/api/lti/courses/115/line_items/95/scores",
            "referrer": None,
            "producer": "canvas",
            "context_type": "Course",
            "context_id": "263480000000000115",
            "context_account_id": "263480000000000001",
            "context_sis_source_id": None,
            "event_name": "submission_created",
            "event_time": "2024-07-09T05:36:48.662Z",
        },
        "body": {
            "submission_id": "263480000000001212",
            "assignment_id": "263480000000000787",
            "user_id": "263480000000000168",
            "submitted_at": "2024-07-08T22:36:20-07:00",
            "lti_user_id": "62c9437ff2a68c2cd499f6516ca435f340a5c635",
            "updated_at": "2024-07-08T22:36:48-07:00",
            "submission_type": "external_tool",
            "attempt": 1,
            "late": False,
            "missing": False,
            "lti_assignment_id": "ff18b98e-6b69-40bf-a5a4-3dede41a2a80",
            "workflow_state": "submitted",
        },
    },
    "submission_updated": {
        "metadata": {
            "context_type": "Course",
            "context_id": "263480000000000106",
            "context_account_id": "263480000000000001",
            "context_sis_source_id": "TEST-102-UPDATED",
            "root_account_uuid": "Ek0vx769rEFEnTt5SqzuGQAoktvvX6K6zfxJiNUH",
            "root_account_id": "263480000000000001",
            "root_account_lti_guid": "Hl5YGmLrMP9CBSgBxdT7OUSKiSDtfxOo6lZqacfh",
            "user_login": "brian.delizza@calbright.org",
            "user_account_id": "263480000000000001",
            "user_sis_id": None,
            "user_id": "263480000000000104",
            "time_zone": "America/Los_Angeles",
            "request_id": "bfa82f78-3cce-4818-b8e2-326a371b75a3",
            "session_id": "ed61c52872366693642f7195af0100a6",
            "hostname": "calbright-dev.instructure.com",
            "http_method": "PUT",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36",
            "client_ip": "47.157.76.180",
            "url": "https://calbright-dev.instructure.com/api/v1/courses/106/assignments/132/submissions/109",
            "referrer": "https://calbright-dev.instructure.com/courses/106/gradebook",
            "producer": "canvas",
            "event_name": "submission_updated",
            "event_time": "2024-04-02T19:22:14.185Z",
        },
        "body": {
            "submission_id": "263480000000000012",
            "assignment_id": "263480000000000132",
            "user_id": "263480000000000109",
            "submitted_at": "2024-03-29T16:45:44-07:00",
            "lti_user_id": "fec513d79409ef7c2f33040adb2238372aa6f17e",
            "graded_at": "2024-04-02T12:22:14-07:00",
            "updated_at": "2024-04-02T12:22:14-07:00",
            "score": 100.0,
            "grade": "100",
            "submission_type": "online_text_entry",
            "body": "<p>yes of course!</p>",
            "attempt": 1,
            "late": False,
            "missing": False,
            "lti_assignment_id": "de278041-464c-4da2-bb2d-7e15ca63a0ef",
            "posted_at": "2024-04-02T12:22:13-07:00",
            "workflow_state": "graded",
        },
    },
    "conversation_created": {
        "metadata": {
            "root_account_uuid": "Ek0vx769rEFEnTt5SqzuGQAoktvvX6K6zfxJiNUH",
            "root_account_id": "263480000000000001",
            "root_account_lti_guid": "Hl5YGmLrMP9CBSgBxdT7OUSKiSDtfxOo6lZqacfh",
            "user_login": "testeroni12357465asd7@calbright.org",
            "user_account_id": "263480000000000001",
            "user_sis_id": "a1",
            "user_id": "263480000000000109",
            "time_zone": "America/Los_Angeles",
            "real_user_id": "263480000000000104",
            "request_id": "0fefc524-e829-4da8-8b63-4642aa1badc4",
            "session_id": "4187f46f2044e71e75935eca9016e2d8",
            "hostname": "calbright-dev.instructure.com",
            "http_method": "POST",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"
            " Chrome/123.0.0.0 Safari/537.36",
            "client_ip": "47.157.76.180",
            "url": "https://calbright-dev.instructure.com/api/graphql",
            "referrer": "https://calbright-dev.instructure.com/conversations",
            "producer": "canvas",
            "event_name": "conversation_created",
            "event_time": "2024-03-29T23:30:23.392Z",
        },
        "body": {"conversation_id": "1", "updated_at": "2024-03-29T16:30:23-07:00"},
    },
    "conversation_message_created": {
        "metadata": {
            "root_account_uuid": "Ek0vx769rEFEnTt5SqzuGQAoktvvX6K6zfxJiNUH",
            "root_account_id": "263480000000000001",
            "root_account_lti_guid": "Hl5YGmLrMP9CBSgBxdT7OUSKiSDtfxOo6lZqacfh",
            "user_login": "testeroni12357465asd7@calbright.org",
            "user_account_id": "263480000000000001",
            "user_sis_id": "a1",
            "user_id": "263480000000000109",
            "time_zone": "America/Los_Angeles",
            "real_user_id": "263480000000000104",
            "request_id": "0fefc524-e829-4da8-8b63-4642aa1badc4",
            "session_id": "4187f46f2044e71e75935eca9016e2d8",
            "hostname": "calbright-dev.instructure.com",
            "http_method": "POST",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
            "hrome/123.0.0.0 Safari/537.36",
            "client_ip": "47.157.76.180",
            "url": "https://calbright-dev.instructure.com/api/graphql",
            "referrer": "https://calbright-dev.instructure.com/conversations",
            "producer": "canvas",
            "event_name": "conversation_message_created",
            "event_time": "2024-03-29T23:30:23.393Z",
        },
        "body": {
            "author_id": "109",
            "conversation_id": "1",
            "created_at": "2024-03-29T16:30:23-07:00",
            "message_id": "1",
        },
    },
    "course_completed": {
        "metadata": {
            "job_id": "1150063701906754",
            "job_tag": "CourseProgress.dispatch_live_event",
            "producer": "canvas",
            "root_account_id": "263480000000000001",
            "root_account_uuid": "Ek0vx769rEFEnTt5SqzuGQAoktvvX6K6zfxJiNUH",
            "root_account_lti_guid": "Hl5YGmLrMP9CBSgBxdT7OUSKiSDtfxOo6lZqacfh",
            "event_name": "course_completed",
            "event_time": "2024-03-29T23:50:52.879Z",
        },
        "body": {
            "progress": {
                "requirement_count": 2,
                "requirement_completed_count": 2,
                "next_requirement_url": None,
                "completed_at": "2024-03-29T23:48:48Z",
            },
            "user": {
                "id": "109",
                "name": "Testeroni McTesterson IIV",
                "email": "testeroni12357465asd7@calbright.org",
            },
            "course": {
                "id": "106",
                "name": "Test Course Propus 2 - Updated",
                "account_id": "1",
                "sis_source_id": "TEST-102-UPDATED",
            },
        },
    },
    "course_progress": {
        "metadata": {
            "job_id": "1150063979871490",
            "job_tag": "CourseProgress.dispatch_live_event",
            "producer": "canvas",
            "root_account_id": "263480000000000001",
            "root_account_uuid": "Ek0vx769rEFEnTt5SqzuGQAoktvvX6K6zfxJiNUH",
            "root_account_lti_guid": "Hl5YGmLrMP9CBSgBxdT7OUSKiSDtfxOo6lZqacfh",
            "event_name": "course_progress",
            "event_time": "2024-04-02T22:19:46.142Z",
        },
        "body": {
            "progress": {
                "requirement_count": 2,
                "requirement_completed_count": 1,
                "next_requirement_url": None,
                "completed_at": None,
            },
            "user": {
                "id": "113",
                "name": "Tony Pizza",
                "email": "tonypizza213445646754676216754@calbright.org",
            },
            "course": {
                "id": "106",
                "name": "Test Course Propus 2 - Updated",
                "account_id": "1",
                "sis_source_id": "TEST-102-UPDATED",
            },
        },
    },
    "course_grade_change": {
        "metadata": {
            "job_id": "1150065120853885",
            "job_tag": "Enrollment.recompute_final_score",
            "producer": "canvas",
            "root_account_id": "263480000000000001",
            "root_account_uuid": "Ek0vx769rEFEnTt5SqzuGQAoktvvX6K6zfxJiNUH",
            "root_account_lti_guid": "Hl5YGmLrMP9CBSgBxdT7OUSKiSDtfxOo6lZqacfh",
            "context_type": "Course",
            "context_id": "263480000000000106",
            "context_account_id": "263480000000000001",
            "context_sis_source_id": "TEST-102-UPDATED",
            "event_name": "course_grade_change",
            "event_time": "2024-04-15T20:46:05.187Z",
        },
        "body": {
            "user_id": "113",
            "course_id": "106",
            "workflow_state": "active",
            "created_at": "2024-04-02T22:15:47Z",
            "updated_at": "2024-04-15T20:46:05Z",
            "current_score": 100.0,
            "old_current_score": None,
            "final_score": 50.0,
            "old_final_score": 0.0,
            "unposted_current_score": 100.0,
            "old_unposted_current_score": None,
            "unposted_final_score": 50.0,
            "old_unposted_final_score": 0.0,
        },
    },
    # "grade_change": {
    #     "metadata": {
    #         "root_account_uuid": "Ek0vx769rEFEnTt5SqzuGQAoktvvX6K6zfxJiNUH",
    #         "root_account_id": "263480000000000001",
    #         "root_account_lti_guid": "Hl5YGmLrMP9CBSgBxdT7OUSKiSDtfxOo6lZqacfh",
    #         "request_id": "92c42d83-b6bd-40e3-b706-469b9cac6328",
    #         "session_id": None,
    #         "hostname": "calbright-dev.instructure.com",
    #         "http_method": "POST",
    #         "user_agent": "GuzzleHttp/7",
    #         "client_ip": "35.168.19.245",
    #         "url": "https://calbright-dev.instructure.com/api/lti/courses/115/line_items/87/scores",
    #         "referrer": None,
    #         "producer": "canvas",
    #         "context_type": "Course",
    #         "context_id": "263480000000000122",
    #         "context_account_id": "263480000000000001",
    #         "context_sis_source_id": None,
    #         "event_name": "grade_change",
    #         "event_time": "2024-07-09T04:30:31.153Z",
    #     },
    #     "body": {
    #         "submission_id": "263480000000001205",
    #         "assignment_id": "263480000000000787",
    #         "assignment_name": "4.0: Summative Assessment",
    #         "grade": "P",
    #         "score": 8.0,
    #         "points_possible": 8.0,
    #         "old_points_possible": 8.0,
    #         "student_id": "263480000000000168",
    #         "grader_id": "263480000000000104",
    #         "student_sis_id": "a111",
    #         "user_id": "263480000000000168",
    #         "grading_complete": True,
    #         "muted": False,
    #     },
    # },
    "grade_change": {
        "metadata": {
            "root_account_uuid": "PKlxiZD7RGmj75tEnfWtzFq1tdp9z70nvnrT6wYL",
            "root_account_id": "246330000000000001",
            "root_account_lti_guid": "hAO1Mtb1dxBDL4ktL9f8DVhSgRChu3VP0zWPPpHw",
            "request_id": "f7a5754c-0b62-4313-9923-e56010117372",
            "session_id": None,
            "hostname": "calbright.instructure.com",
            "http_method": "POST",
            "user_agent": "GuzzleHttp/7",
            "client_ip": "35.168.19.245",
            "url": "https://calbright.instructure.com/api/lti/courses/336/line_items/1448/scores",
            "referrer": None,
            "producer": "canvas",
            "context_type": "Course",
            # "context_id": "246330000000000336",
            # "context_id": "246330000000000902",
            "context_id": "902",
            "context_account_id": "246330000000000124",
            "context_sis_source_id": "bus500",
            "event_name": "grade_change",
            "event_time": "2024-07-23T17:49:26.934Z",
        },
        "body": {
            "submission_id": "263480000000001205",
            "assignment_id": "24633000000000784",
            "assignment_name": "1.0: Milestone Activity",
            "grade": "100%",
            "score": 11.0,
            "points_possible": 11.0,
            "old_points_possible": 11.0,
            "student_id": "263480000000000168",
            "student_sis_id": "TST0010",
            "user_id": "263480000000000168",
            "grading_complete": True,
            "muted": False,
        },
    },
    "grade_override": {},
    "logged_in": {
        "metadata": {
            "root_account_uuid": "Ek0vx769rEFEnTt5SqzuGQAoktvvX6K6zfxJiNUH",
            "root_account_id": "263480000000000001",
            "root_account_lti_guid": "Hl5YGmLrMP9CBSgBxdT7OUSKiSDtfxOo6lZqacfh",
            "request_id": "0abcb460-263e-49bd-b3d9-91e0ff9b3819",
            "session_id": "93a719d70bd9cc4b567e6ce05663abdb",
            "hostname": "calbright-dev.instructure.com",
            "http_method": "POST",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"
            " Chrome/124.0.0.0 Safari/537.36",
            "client_ip": "76.32.250.25",
            "url": "https://calbright-dev.instructure.com/login/saml",
            "referrer": "https://login.calbright.org/",
            "producer": "canvas",
            "user_id": "263480000000000104",
            "user_login": "brian.delizza@calbright.org",
            "user_account_id": "263480000000000001",
            "user_sis_id": None,
            "event_name": "logged_in",
            "event_time": "2024-05-10T20:39:26.747Z",
        },
        "body": {},
    },
    "quiz_submitted": {
        "metadata": {
            "context_type": "Course",
            "context_id": "263480000000000113",
            "context_account_id": "263480000000000001",
            "context_sis_source_id": None,
            "root_account_uuid": "Ek0vx769rEFEnTt5SqzuGQAoktvvX6K6zfxJiNUH",
            "root_account_id": "263480000000000001",
            "root_account_lti_guid": "Hl5YGmLrMP9CBSgBxdT7OUSKiSDtfxOo6lZqacfh",
            "user_login": "tony.pizza@calbright.org",
            "user_account_id": "263480000000000001",
            "user_sis_id": "a1",
            "user_id": "263480000000000134",
            "time_zone": "America/Los_Angeles",
            "real_user_id": "263480000000000104",
            "context_role": "StudentEnrollment",
            "request_id": "5f78eff7-6536-43e1-b3b8-d1b6a7ea659e",
            "session_id": "1b9c812ea0278d4b03913f4ad428e1b4",
            "hostname": "calbright-dev.instructure.com",
            "http_method": "POST",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36",
            "client_ip": "104.172.197.20",
            "url": "https://calbright-dev.instructure.com/courses/113/quizzes/129/submissions?user_id=134",
            "referrer": "https://calbright-dev.instructure.com/courses/113/quizzes/129/take",
            "producer": "canvas",
            "event_name": "quiz_submitted",
            "event_time": "2024-06-29T03:41:07.311Z",
        },
        "body": {"submission_id": "263480000000000004", "quiz_id": "263480000000000129"},
    },
}
