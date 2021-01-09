{%- set filters_applied = namespace(val=False) -%}
{%- if vars.vacation_settings and not vars.vacation_settings["alwaysSend"] and vars.filter_settings -%}
{%- for filter in vars.filter_settings -%}
{{ filter }}
{%- endfor -%}
{%- set filters_applied.val = True -%}
{%- endif -%}

{%- if vars.vacation_settings -%}
require ["vacation","date","relational"];
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
if allof (header :contains "subject" "yartu") {
    discard;
}
{%- endif -%}

{%- if vars.forward_settings -%}
{%- for mail in vars.forward_settings.target_emails -%}
redirect "{{ mail }}";
{%- endfor -%}
{%- if vars.forward_settings.keep_copy -%}
keep;
{%- endif -%}
{%- endif -%}
