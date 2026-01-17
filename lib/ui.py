from tabulate import tabulate


class Table:
    def __init__(self, args, items, columns):
        self.verbosity = 0  # TODO: from args
        self.items = list(items)
        self.columns = {}
        default = {
            'verbosity': 0,
            'getter': lambda i, k: getattr(i, k, None),
            'formatter': lambda v: '' if v is None else v,
            'formatter_nonempty': lambda v: v,
        }
        for k, v in columns.items():
            if isinstance(v, str):
                v = {'label': v}
            self.columns[k] = dict(default, **v)


    def render(self):
        columns = {k: c for k, c in self.columns.items() if c['verbosity'] <= self.verbosity}
        headers = [c['label'] for c in columns.values()]
        rows = []
        for i in self.items:
            r = []
            for k, c in columns.items():
                v = c['getter'](i, k)
                if v is not None:
                    v = c['formatter_nonempty'](v)
                else:
                    v = c['formatter'](v)
                r.append(v)
            rows.append(r)
        return tabulate(rows, headers=headers)

    def __str__(self):
        return self.render()
