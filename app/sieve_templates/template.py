from flask import render_template

class Template(object):

    def __init__(self, name, params):
        self.name = name
        self.params = params

    def render(self):
        return render_template(self.name, vars=self.params)
