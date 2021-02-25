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
import json
import subprocess

def get_vacation_vars(data):
    requirements = ["vacation","date","relational"]

    payload = {}
    payload["enabled"] = data.enabled

    vacation_data = data.value

    payload["daysBetweenResponse"] = vacation_data.get('days_beetwen_response', 7)
    payload["startDateEnabled"] = vacation_data.get('enable_auto_reply', False)
    payload["startDate"] = vacation_data.get('enable_reply_on', '')
    payload["endDateEnabled"] = vacation_data.get('disable_auto_reply', False)
    payload["endDate"] = vacation_data.get('disable_reply_on', '')
    # Sending/Recieving options
    payload["ignoreLists"] = vacation_data.get('ignore_lists', False)
    payload["alwaysSend"] = vacation_data.get('always_vacation_message_response', True)
    payload["discardMails"] = vacation_data.get('discard_incoming_mails', False)
    #  Content options
    payload["customSubjectEnabled"] = (vacation_data.get('subject', False) != False)
    payload["customSubject"] = vacation_data.get('subject', False)
    payload["autoReplyText"] = vacation_data.get('message', '')
    payload["autoReplyEmailAddresses"] = ', '.join('"{0}"'.format(mail_addr['email']) for mail_addr in vacation_data.get('accounts'))
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
        "match_any_flowing_rules": "anyof",
        "match_all_flowing_rules": "allof",
        "match_all": "all",
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

    filter_negative_conditions = {
        "is_not": ":is",
        "does_not_contain": ":contains",
        "does_not_match": ":matches",
        "does_not_match_regex": ":regex"
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
        "discard_message": "discard",
        "keep_message": "keep",
        "stop_processing_filter": "stop",
        "forward_message_to": "redirect",
        "send_reject_message": "reject",
        "file_message_in": "fileinto"
    }

    action_value_map = {
        "forward_message_to": "to_email",
        "send_reject_message": "message",
        "file_message_in": "folder"
    }

    filters = data.value

    raw_filter = ""
    fs = FiltersSet("cow")
    filters = sorted(filters, key=lambda f: f['order'])
    for s_filter in filters:# range(len(filters.keys())):
        # filter= filters[i]
        filter_name = s_filter.get("name")
        enabled = True # s_filter.get("enabled") TODO :: 
        rules = s_filter.get("conditions")
        actions = s_filter.get("actions")
        matchtype = filter_match_types[s_filter.get("incoming_message")]

        builded_conditions = []
        for rule in rules: # range(len(rules.keys())):
            # rule = rules[rule_number]
            negated = False
            section = filter_sections[rule["selector"]]
            if "not" in rule["condition"]:
                negated = True
                condition = filter_negative_conditions[rule["condition"]]
            else:
                condition = filter_conditions[rule["condition"]]

            condition = filter_section_conditions[section](condition)

            if negated:
                section = "not{}".format(section)

            value = rule["value"]
   
            builded_conditions.append((section, *condition, value))

        builded_actions = []
        actions = sorted(actions, key=lambda f: f['order'])
        for action in actions:# range(len(actions.keys())):
            # action = actions[action_number]
            param = ""
            if action["type"] in action_value_map.keys():
                param = action[action_value_map[action["type"]]]
            # if value_map=[]
            builded_actions.append((filter_actions[action["type"]], param))

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
            fs.addfilter(name=filter_name, conditions=builded_conditions, actions=builded_actions, matchtype=matchtype)

    requirements = fs.requires
    io = StringIO()
    fs.tosieve(io)
    raw_sieve = io.getvalue()
    if requirements:
        raw_sieve = '\n'.join(raw_sieve.splitlines()[2:])

    if "not" in raw_sieve:
        for key in filter_sections.keys():
            raw_sieve = raw_sieve.replace("not" + key, key)

    return [raw_sieve, requirements]

def get_forward_vars(data):
    """
    data = {
        "emails": ["abc@example.com", "def@example.com"], # List
        "keep_a_copy": True # Boolean 
    }
    """
    requirements = []
    forward_data = data.value
    payload = {}

    payload["target_emails"] = forward_data.get("emails")
    payload["keep_copy"] = forward_data.get("keep_a_copy", False)

    return [payload, requirements]

def create_sieve_script():

    main_user = session.get('main_user', None)

    if not main_user:
        raise False

    username = main_user['email']
    password = main_user['password']

    user = User.query.filter(User.username == username).first()

    # Get user vacation Settings
    vacation_settings = (Settings.query.filter(Settings.enabled == True).filter(Settings.section == "email").filter(Settings.setting_type == "email-vacation").first()) or False

    # Get user filter settings
    filter_settings = (Settings.query.filter(Settings.section == "email").filter(Settings.setting_type == "email-filters").first()) or False

    # Get user forwarding settings
    forward_settings = (Settings.query.filter(Settings.enabled == True).filter(Settings.section == "email").filter(Settings.setting_type == "email-forward").first()) or False

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
