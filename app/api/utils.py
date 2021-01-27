from app import app, db, jwt
from app.api.models import User, Account, Settings
from app.sieve_templates.template import Template
from flask import render_template
from flask import session
from sievelib.managesieve import Client
from sievelib.factory import FiltersSet
from sievelib.parser import Parser
from io import StringIO

import sys
import traceback
import subprocess

def get_vacation_vars(data):
    requirements = ["vacation","date","relational"]

    payload = {}
    payload["enabled"] = data.get('enabled', True)
    # Date Settings
    payload["daysBetweenResponse"] = data.get('daysBetweenResponse', 7)
    payload["startDateEnabled"] = data.get('startDateEnabled', False)
    payload["startDate"] = data.get('startDate')
    payload["endDateEnabled"] = data.get('endDateEnabled', False)
    payload["endDate"] = data.get('endDate')
    # Sending/Recieving options
    payload["ignoreLists"] = data.get('ignoreLists', False)
    payload["alwaysSend"] = data.get('alwaysSend', True)
    payload["discardMails"] = data.get('discardMails')
    #  Content options
    payload["customSubjectEnabled"] = data.get('customSubjectEnabled', False)
    payload["customSubject"] = data.get('customSubject', False)
    payload["autoReplyText"] = data.get('autoReplyText')
    payload["autoReplyEmailAddresses"] = ', '.join('"{0}"'.format(mail_addr) for mail_addr in data.get('autoReplyEmailAddresses'))
    payload["conditions_enabled"] =  (payload["startDateEnabled"] or payload["endDateEnabled"] or payload["ignoreLists"])

    if payload["conditions_enabled"]:
        conditions = []
        if payload["startDateEnabled"]:
            start_date_condition = 'currentdate :value "ge" "date" "{}"'.format(payload["startDate"]) # Date format: YYYY-MM-DD
            conditions.append(start_date_condition)
        if payload["endDateEnabled"]:
            end_date_condition = 'currentdate :value "le" "date" "{}"'.format(payload["endDate"]) # Date format: YYYY-MM-DD
            conditions.append(end_date_condition)
        if payload["ignoreLists"]:
            ignore_list_conditions = 'not exists ["list-help", "list-unsubscribe", "list-subscribe", "list-owner", "list-post", "list-archive", "list-id", "Mailing-List"], not header :comparator "i;ascii-casemap" :is "Precedence" ["list", "bulk", "junk"], not header :comparator "i;ascii-casemap" :matches "To" "Multiple recipients of*"'
            conditions.append(ignore_list_conditions)
        payload["conditions"] = ','.join(conditions)
    return [payload, requirements]

def get_filter_vars(data):
    filter_match_types = {
        "anyof": "anyof",
        "allof": "allof",
        "all": "all",
    }

    filter_sections = {
        "subject": "subject",
        "from": "from",
        "to": "to",
        "cc": "cc",
        "to_or_cc": "to_or_cc",
        "size": "size",
        "header": "header",
        "body": "body"
    }

    filter_conditions = {
        "is": ":is",
        "contains": ":contains",
        "matches": ":matches",
        "matches_regex": ":regex",
        "is_under": ":over",
        "is_over": ":under",
    }

    filter_section_conditions = {
        "subject": lambda x: [x],
        "from": lambda x: [x],
        "to": lambda x: [x],
        "cc": lambda x: [x],
        "to_or_cc": lambda x: [x],
        "size": lambda x: [x],
        "header": lambda x: [x],
        "body": lambda x: [":text", x]
    }

    filter_actions = {
        "discard": "discard",
        "keep": "keep",
        "stop_filter_proc": "stop",
        "forward_to": "redirect",
        "send_reject_msg": "reject",
        "fileinto": "fileinto"
    }

    filters = data.get("content")

    raw_filter = ""
    for i in range(len(filters.keys())):
        filter= filters[i]
        filter_name = filter.get("filter_name")
        enabled = filter.get("enabled")
        rules = filter.get("rules")
        actions = filter.get("actions")
        matchtype = filter_match_types[filter.get("match_with")]

        fs = FiltersSet(filter_name)
        builded_conditions = []
        for rule_number in range(len(rules.keys())):
            rule = rules[rule_number]
            negated = rule["negated"]
            section = filter_sections[rule["section"]]
            if negated:
                section = "not{}".format(section)
            condition = filter_conditions[rule["condition"]]
            condition = filter_section_conditions[section](condition)
            value = rule["value"]
            builded_conditions.append((section, *condition, value))

        builded_actions = []
        for action_number in range(len(actions.keys())):
            action = actions[action_number]
            builded_actions.append((filter_actions[action["name"]], action["param"]))

        if matchtype == "all":
            p = Parser()
            raw = 'require ["reject","fileinto","imap4flags"];'
            for builded_action in builded_actions:
                name = builded_action[0]
                param = builded_action[1]
                if param:
                    raw += "\n{} \"{}\";".format(name, param)
                else:
                    raw += "\n{};".format(name)
            p.parse(raw)
            fs.from_parser_result(p)
        else:
            fs.addfilter(name=filter_name, conditions=builded_conditions, actions=builded_actions, matchtype="allof")

    requirements = fs.requires
    io = StringIO()
    fs.tosieve(io)
    raw_sieve = io.getvalue()
    raw_sieve = '\n'.join(raw_sieve.splitlines()[2:])
    return [raw_sieve, requirements]

def get_forward_vars(data):
    """
    data = {
        "target_emails": ["abc@example.com", "def@example.com"], # List
        "keep_copy": True # Boolean 
    }
    """
    requirements = ""

    payload = {}
    payload["target_mails"] = data.get("target_emails", )
    payload["keep_copy"] = data.get("keep_copy", False)

    return payload, requirements

def create_sieve_script():

    main_user = session.get('main_user', None)

    if not main_user:
        raise False

    username = main_user['email']
    password = main_user['password']

    user = User.query.filter(User.username == username).first()

    # Get user vacation Settings
    vacation_settings = (Settings.query.filter(Settings.enabled == True).filter(Settings.section == "mail").filter(Settings.setting_type == "vacation").first()) or False

    # Get user filter settings
    filter_settings = (Settings.query.filter(Settings.enabled == True).filter(Settings.section == "mail").filter(Settings.setting_type == "filter").first()) or False

    # Get user forwarding settings
    forward_settings = (Settings.query.filter(Settings.enabled == True).filter(Settings.section == "mail").filter(Settings.setting_type == "forward").first()) or False

    sieve_payload = {}
    sieve_reqs = []

    if vacation_settings:
        vs = get_vacation_vars(vacation_settings)
        sieve_payload["vacation_settings"] = vs[0]
        sieve_reqs = sieve_reqs + vs[1]
    else:
        sieve_payload["vacation_settings"] = False

    if filter_settings:
        fs = get_filter_vars(filter_settings)
        sieve_payload["filter_settings"] = fs[0]
        sieve_reqs = sieve_reqs + fs[1]
    else:
        sieve_payload["filter_settings"] = False

    if forward_settings:
        fs = get_forward_vars(forward_settings)
        sieve_payload["forward_settings"] = fs[0]
        sieve_reqs = sieve_reqs + fs[1]
    else:
        sieve_payload["forward_settings"] = False

    sieve_payload["requirements"] = ', '.join('"{0}"'.format(req) for req in sieve_reqs)
    # connect to the managesieve host
    client = Client(app.config['IMAP_HOST'])
    client.connect(username, password, starttls=True, authmech="PLAIN")
    script = Template("cowui.sieve", sieve_payload).render()
    client.setactive("")
    client.deletescript("cowui")
    client.putscript("cowui", script)
    client.setactive("cowui")
    client.logout()
