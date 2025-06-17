import re

class MyBehavior(object):
    def __init__(self, action, check, context):
        self.action = action # string
        self.check = check # bool
        self.context = context # dict

    def __str__(self):
        result = self.fmt_action()
        if self.check:
            result += ' ^check'
        return result

    def fmt_action(self):
        if not self.action:
            return ''

        if 'source' in  self.context:
            source_name = self.context['source']
            auto_source = source_name[0].lower() + source_name[1:]
        else:
            auto_source = ''

        if 'target' in  self.context:
            target_name = self.context['target']
            auto_target = target_name[0].lower() + target_name[1:]
        else:
            auto_target = ''

        event = ''
        if 'event' in  self.context and self.context['event'] \
            and self.context['event'] != 'Check':
            event = self.context['event']
            auto_event = event[0].upper() + event[1:]
        elif 'guard' in self.context and self.context['guard']:
            guard = self.context['guard']
            if guard[0] == '!':
                guard = guard[1:]
                not_prefix = 'Not'
            else:
                not_prefix = ''
            auto_event = not_prefix + guard[0].upper() + guard[1:]
        else:
            auto_event = ''

        if event == 'entry':
           auto_action1 = auto_source + 'Entry'
        elif event == 'exit':
           auto_action1 = auto_source + 'Exit'
        else:
           auto_action1 = auto_source + 'On' + auto_event

        auto_action2 = auto_source + 'On' + auto_event

        return re.sub(r'%a', auto_action1,
               re.sub(r'%b', auto_action2,
               re.sub(r'%s', auto_source,
               re.sub(r'%t', auto_target,
               re.sub(r'%E', auto_event, self.action)))))

