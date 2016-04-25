from sqlalchemy import *

CONN_URL = "postgresql://yoavnathaniel:BrokeFoot420!!@localhost"

DB_SCHEMA = "records_db"


DEFAULT_OBJECT_NAMES = [
    "_Dynamic_Apis",
    "_User_Management",
    "_Alert_Rules",
    "_Alert_Finds"
]



DYNAMIC_API_OBJECT_NAME = "_Dynamic_Apis"

DYNAMIC_API_PROPERTIES = [
    {
        "name": "object_name",
        "type": Unicode,
        "unique": True,
        "nullable": False
    },
    {
        "name": "api_url",
        "type": Unicode,
        "unique": True,
        "nullable": False
    }
]

USER_MANAGEMENT_OBJECT_NAME = "_User_Management"

USER_MANAGEMENT_PROPERTIES = [
    {
        "name": "name",
        "type": Unicode,
        "unique": False,
        "nullable": True
    },
    {
        "name": "email",
        "type": Unicode,
        "unique": True,
        "nullable": False
    },
    {
        "name": "password",
        "type": Unicode,
        "unique": False,
        "nullable": False
    },
    {
        "name": "hidden_from_ui",
        "type": Boolean,
        "unique": False,
        "nullable": False
    },
    {
        "name": "is_admin",
        "type": Boolean,
        "unique": False,
        "nullable": False
    }
]

ALERT_RULES_OBJECT_NAME = "_Alert_Rules"

ALERT_RULES_PROPERTIES = [
    {
        "name": "name",
        "type": Unicode,
        "unique": False,
        "nullable": False
    },
    {
        "name": "object_name",
        "type": Unicode,
        "unique": False,
        "nullable": False
    },
    {
        "name": "column_name",
        "type": Unicode,
        "unique": False,
        "nullable": False
    },
    {
        "name": "column_value",
        "type": Unicode,
        "unique": False,
        "nullable": True
    }
]

ALERT_FINDS_OBJECT_NAME = "_Alert_Finds"

ALERT_FINDS_PROPERTIES = [
    {
        "name": "rule_name",
        "type": Unicode,
        "unique": False,
        "nullable": False
    },
    {
        "name": "object_name",
        "type": Unicode,
        "unique": False,
        "nullable": False
    },
    {
        "name": "column_name",
        "type": Unicode,
        "unique": False,
        "nullable": False
    },
    {
        "name": "found_value",
        "type": Unicode,
        "unique": False,
        "nullable": True
    },
    {
        "name": "found_id",
        "type": Unicode,
        "unique": True,
        "nullable": False
    },
]