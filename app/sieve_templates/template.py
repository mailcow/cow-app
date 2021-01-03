from flask import render_template

class Template(object):

    def __init__(self, name, params):
        self.name = name
        self.params = params

    def render():
        raw_template = get_attr()
        return render_template(raw_template, vars=params)
