# utils/chat_intents.py

FUZZY_THRESHOLD = 0.75

INTENTS = {
    "ATTENDANCE": {
        "keywords": ["attendance", "attendence", "attend", "present"],
        "source": "DB"
    },

    "FEES": {
        "keywords": ["fee", "fees", "payment", "amount", "scholarship", "scholarships"],
        "source": "DB"
    },

    "ADMISSION": {
        "keywords": ["admission", "admissions", "enrollment", "enroll", "join"],
        "source": "FAQ"
    },

    "TODAY_CLASSES": {
        "phrases": [
            "today class",
            "today classes",
            "today timetable",
            "class today"
        ],
        "source": "DB"
    },

    "CLASS_TEACHER": {
        "phrases": [
            "who is my class teacher",
            "class teacher",
            "my class teacher",
            "who is our class teacher"
        ],
        "keywords": ["class teacher"],
        "source": "DB"
    },

    "FACULTY_DETAILS": {
        "keywords": ["faculty details", "teacher detail", "professor", "prof", "details of faculty", "detail of any faculty"],
        "source": "FAQ"
    },

    "NEXT_CLASS": {
        "phrases": [
            "next class",
            "next lecture",
            "upcoming class"
        ],
        "source": "DB"
    },

    "TIMETABLE": {
        "keywords": ["timetable", "schedule", "class", "lecture"],
        "source": "DB"
    },

    "COLLEGE_INFO": {
        "keywords": ["rule", "policy", "office", "library"],
        "source": "FAQ"
    },

    "ELIGIBILITY": {
        "keywords": ["eligible", "eligibility"],
        "source": "DB"
    },

    "ALERTS": {
        "keywords": ["alert", "warning"],
        "source": "DB"
    },

    "JOKE": {
        "keywords": ["joke"],
        "source": "FUN"
    }
}
