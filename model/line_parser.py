import re


class LineParser(object):
    def __init__(self, reg_exp, pass1_handler, pass2_handler, kind):
        self.reg_exp = re.compile(reg_exp)
        self.pass_handlers = (pass1_handler, pass2_handler)
        self.kind = kind