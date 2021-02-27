import re

EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

schema = {
    "email-general": {
        "browser_notification": {
            "required": True,
            "field_type": bool,
            "rules": lambda i: type(i) is bool
        },
        "auto_refresh_every": {
            "required": True,
            "field_type": str,
            "rules": lambda i: (type(i) is str and i in ["1m" ,"5m", "10m", "30m", "1h"])
        }
    },
    "email-vacation": {
        "enabled": {
            "required": True,
            "field_type": bool,
            "rules": lambda i: type(i) is bool
        },
        "subject": {
            "required": False,
            "field_type": str,
            "rules": lambda i: (type(i) is str and len(i) > 0 and len(i) < 128)
        },
        "days_beetwen_response": {
            "required": True,
            "field_type": int,
            "rules": lambda i: (type(i) is int and i > 0 and i < 8)
        },
        "message": {
            "required": True,
            "field_type": str,
            "rules": lambda i: (type(i) is str and len(i) > 1 and len(i) < 1024)
        },
        "ignore_lists": {
            "required": False,
            "field_type": bool,
            "rules": lambda i: type(i) is bool
        },
        "enable_reply_on": {
            "required": False,
            "field_type": "str",
            "rules": lambda i: (type(i) is str and len(i) > 0 and len(i) < 64)
        },
        "disable_reply_on": {
            "required": False,
            "field_type": "str",
            "rules": lambda i: (type(i) is str and len(i) > 0 and len(i) < 64)
        },
        "always_vacation_message_response": {
            "required": False,
            "field_type": bool,
            "rules": lambda i: type(i) is bool
        },
        "discard_incoming_mails": {
            "required": False,
            "field_type": bool,
            "rules": lambda i: type(i) is bool
        }
    },
    "email-forward": {
        "enabled": {
            "required": True,
            "field_type": bool,
            "rules": lambda i: type(i) is bool
        },
        "emails": {
            "required": True,
            "field_type": list,
            "rules": lambda i : type(i) is list,
            "sub": {
                "field_type": str,
                "rules": lambda i: (type(i) is str and EMAIL_REGEX.match(i))
            }
        },
        "keep_a_copy": {
            "required": False,
            "field_type": bool,
            "rules": lambda i: type(i) is bool
        }
    },
    "email-filters": {
        "order": {
            "required": True,
            "field_type": int,
            "rules": lambda i: (type(i) is int and i >= 0)
        },
        "name": {
            "required": True,
            "field_type": str,
            "rules": lambda i: (type(i) is str and len(i) > 1 and len(i) < 128)
        },
        "incoming_message": {
            "required": True,
            "field_type": str,
            "rules": lambda i: (type(i) is str and i in ["match_all_flowing_rules", "match_any_flowing_rules", "match_all"])
        },
        "conditions": {
            "required": False,
            "field_type": list,
            "rules": lambda i : type(i) is list,
            "sub": {
                "field_type": dict, # dict: dict list | int: int list ..etc
                # "rules" # Just use withour dict list
                "selector": {
                    "field_type": str,
                    "rules": lambda i : (type(i) is str and i in ["subject", "from", "to", "cc", "to_or_cc", "size", "header", "body"])
                },
                "condition": {
                    "field_type": str,
                    "rules": lambda i : (type(i) is str and i in ["is", "is_not", "is_under", "is_over", "contains", "does_not_contain", "matches", "does_not_match", "matches_regex", "does_not_match_regex"])
                },
                "value": {
                    "field_type": str,
                    "rules": lambda i : (type(i) is str and len(i) > 0 and len(i) < 256)
                },
               "header": {
                    "field_type": str,
                    "rules": lambda i : (type(i) is str and len(i) > 0 and len(i) < 256)
                }
            }
        },
        "actions": {
            "required": False,
            "field_type": list,
            "rules": lambda i : type(i) is list,
            "sub": {
                "field_type": dict, # dict: dict list | int: int list ..etc
                # "rules" # Just use withour dict list
                "type": {
                    "field_type": str,
                    "rules": lambda i: (type(i) is str and i in ["discard_message", "keep_message", "stop_processing_filter", "forward_message_to", "send_reject_message", "file_message_in", "file_message_with"])
                },
                "to_email": {
                    "field_type": str,
                    "rules": lambda i: (type(i) is str and EMAIL_REGEX.match(i))
                },
                "folder": {
                    "field_type": str,
                    "rules": lambda i: (type(i) is str)
                },
                "file_width": {
                    "field_type": str,
                    "rules": lambda i: (type(i) is str and i in ["seen", "deleted", "answered", "flagged", "junk", "not_junk", "work", "later", "important", "todo", "return_receipt_sent", "personal"])
                },
                "message": {
                    "field_type": str,
                    "rules": lambda i: (type(i) is str and len(i) > 0 and len(i) < 1024)
                }
            }
        }
    }
}


