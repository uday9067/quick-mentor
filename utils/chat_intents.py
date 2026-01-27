# utils/chat_intents.py

FUZZY_THRESHOLD = 0.75

INTENTS = {
    "ATTENDANCE": {
        "keywords": ["attendance", "attendence", "attend", "present"],
        "source": "DB"
    },

    "FEES": {
        "keywords": ["fee", "fees", "payment", "amount"],
        "source": "DB"
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
