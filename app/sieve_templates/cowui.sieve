{%- if vars.requirements -%}
require [{{ vars.requirements }}];
{%- endif -%}

{%- set filters_applied = namespace(val=False) -%}
{%- if vars.vacation_settings and not vars.vacation_settings["alwaysSend"] and vars.filter_settings -%}
{{ vars.filter_settings }}
{%- set filters_applied.val = True -%}
{%- endif -%}

{%- if vars.vacation_settings -%}
{% if vars.vacation_settings["conditions_enabled"] %}
if allof ( {{ vars.vacation_settings["conditions"] }} ) {
{%- endif -%}
vacation
:days {{ vars.vacation_settings["daysBetweenResponse"] }}
{%- if vars.vacation_settings["customSubjectEnabled"] -%}
:subject "{{ vars.vacation_settings["customSubject"] }}"
{%- endif -%}
:addresses [{{ vars.vacation_settings["autoReplyEmailAddresses"] }}]
text:
{{ vars.vacation_settings["autoReplyText"] }}
.
;
{%- if vars.vacation_settings["discardMails"] -%}
discard;
{%- endif -%}
{%- if vars.vacation_settings["conditions_enabled"] -%}
}
{%- endif -%}
{%- endif -%}

{%- if vars.filter_settings and not filters_applied.val %}
{{ vars.filter_settings }}
{%- endif -%}

{%- if vars.forward_settings -%}
{% for mail in vars.forward_settings.target_emails %}
redirect "{{ mail }}";
{% endfor %}
{%- if vars.forward_settings.keep_copy -%}
keep;
{%- endif -%}
{%- endif -%}
