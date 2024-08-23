def format_grade_level(code: str):
    """Formats the grade level id that would be used for Anthology based on what comes from CCCApply

    Args:
        code (str): CCCApplies highest_grade_level[0] value since the string returned is grade_yyyy. ex. "82020"

    Returns:
        int: grade level id to use for SIS (Anthology) calls
    """
    grade_level_options = {
        "X": 2,
        "7": 4,
        "8": 7,
    }

    return grade_level_options.get(code, 1)


def filter_check(model_key, check_value):
    return model_key == check_value if check_value else None


def format_edu_goal(code):
    edu_goal_options = {
        "A": "Obtain an associate degree and transfer to a 4-year institution",
        "B": "Transfer to a 4-year institution without an associate degree",
        "C": "Obtain a 2-year associate degree without transfer",
        "D": "Obtain a 2-year technical degree without transfer",
        "E": "Earn a career technical certificate without transfer",
        "F": "Discover/Formulate career interests, plans, goals",
        "G": "Prepare for a new career (acquire job skills)",
        "H": "Advance in current job/career (update job skills)",
        "I": "Maintain certificate or license",
        "J": "Educational development",
        "K": "Improve basic skills",
        "L": "Complete credits for high school diploma or GED",
        "M": "Undecided on goal",
        "N": "To move from noncredit coursework to credit coursework",
        "O": "4 year college student taking courses to meet 4 year college requirements",
    }

    return edu_goal_options.get(code, None)


def format_gender(code):
    gender_options = {"F": "Female", "M": "Male", "B": "Non-binary", "X": "Decline to State", None: "No Selection"}

    return gender_options.get(code, None)


def format_ethnicity(code):
    ethnicity_options = {
        0: "Hispanic, Latino",
        1: "Mexican, Mexican-American, Chicano",
        2: "Central American",
        3: "South American",
        4: "Hispanic Other",
        5: "Asian Indian",
        6: "Asian Chinese",
        7: "Asian Japanese",
        8: "Asian Korean",
        9: "Asian Laotian",
        10: "Asian Cambodian",
        11: "Asian Vietnamese",
        12: "Asian Filipino",
        13: "Asian Other",
        14: "Black or African American",
        15: "American Indian / Alaskan Native",
        16: "Pacific Islander Guamanian",
        17: "Pacific Islander Hawaiian",
        18: "Pacific Islander Samoan",
        19: "Pacific Islander Other",
        20: "White",
    }

    return [ethnicity_options.get(i, None) for i, v in enumerate(code) if v == "Y"]
