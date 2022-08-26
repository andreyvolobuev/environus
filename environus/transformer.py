from .var import Var


class Transformer:
    def __init__(self, data: dict):
        self.data = sorted(data, key=lambda x: (str(x['group']), str(x['title'])))
        self.longest = self.get_longest()

    def get_longest(self):
        longest = {}
        for item in self.data:
            for k, v in item.items():
                result = longest.get(k, 0)
                long_ = max(len(str(k)), len(str(v)))
                if long_ > result:
                    result = long_
                longest[k] = result
        return longest

    def draw_line(self, c='-'):
        line = '+'
        for slot in Var.__slots__:
            line += c + (self.longest[slot] * c) + c + '+'
        return line

    def draw_row(self, item):
        line = '|'
        for slot in Var.__slots__:
            v = str(item[slot])
            line += ' ' + v
            line += (self.longest[slot] - len(v) + 1) * ' '
            line += '|'
        return line

    def draw_head(self):
        head = self.draw_line() + '\n'
        head += self.draw_row({i: i for i in Var.__slots__}) + '\n'
        head += self.draw_line(c='=') + '\n'
        return head

    def draw_table(self):
        line = self.draw_head()
        for i, item in enumerate(self.data):
            line += self.draw_row(item) + '\n'
            line += self.draw_line()
            if i+1 < len(self.data):
                line += '\n'
        return line

    def spit_groups(self):
        group = None
        items = []
        for item in self.data:
            if item['group'] != group:
                group = item['group']
                if len(items) > 0:
                    yield items
                items = []
            items.append(item)
        yield items

    def draw_list(self):
        yield 'Environment variables'
        yield '=====================\n'
        yield 'Here\'s a list of currently used variables.'

        yield 'Please note: \n'
        yield '* all variables with required=True have to be set within the deployment'
        yield '* all variables will be cast to the corresponding type'
        yield '* corresponding default value of a variable will be used if the variable is unset\n'

        for group in self.spit_groups():
            group_name = group[0]['group'] or 'the rest...'
            yield group_name
            yield '+' * len(str(group_name)) + '\n'
            for i, item in enumerate(group):
                yield f'{i+1}. **%s**::\n' % item['title']
                yield '       %s' % (item['description'] or '')
                yield '       _____________________________________________'
                yield '       required: %s | type: %s | default: %s\n\n' % (
                    item['required'], item['type'], item['default']
                )
            yield '\n'

    def render(self,):
        yield 'Environment variables'
        yield '====================='
        yield '\n'

        yield "Here's a table of currently used variables."
        yield '*Please note that all variables with required=True have to be set*'
        yield '\n'

        yield self.draw_table()

        yield '\n\n'

    def to_rst(self, filename):
        with open(filename, "w+") as f:
            for line in self.draw_list():
                f.write(str(line) + '\n')
        print('done!')
