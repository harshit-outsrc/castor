def test_retrieve_calbright_user(self):
    attendee, user = self.calendly.retrieve_calbright_user(self.calendly_id_url, self.user_email)
    self.assertIsNone(attendee)
    self.assertEqual(user, self.calendly_id_url)
    attendee, user = self.calendly.retrieve_calbright_user()
    self.assertIsNone(attendee)
    self.assertIsNone(user)

    for t_name in ["counselor", "student_services"]:
        self.test_name = t_name
        attendee, user = self.calendly.retrieve_calbright_user(self.calendly_id_url, self.user_email)
        self.assertEqual(attendee, self.user_id)
        self.assertEqual(user, self.calendly_id_url)


def sf_custom_query(self, query):
    if "User" in query:
        self.assertEqual(
            query,
            "SELECT Id, Title, Email FROM User WHERE Email = 'prof@calbright.org'",
        )
        if self.test_name == "counselor":
            return {"records": [{"Id": self.user_id, "Title": "Student Counselor For Future"}]}
        if self.test_name in ["student_services", "successful_run"]:
            return {"records": [{"Id": self.user_id, "Title": "All Student Support Services"}]}
        return {"records": []}

    self.assertEqual(
        query,
        "Select Id FROM contact WHERE Email = 'you@me.com'\n        OR cfg_Calbright_Email__c = 'you@me.com'",
    )
    if self.test_name == "no_matching_student":
        return {"totalSize": 0}
    return {"totalSize": 2, "records": [{"Id": self.salesforce_id}]}
