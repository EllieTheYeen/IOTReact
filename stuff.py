listeners = []

class listener(object):
    def __init__(self, channel=None, pattern=None, sync=False, out=None):
        if channel is None and pattern is None:
            raise ValueError('Must have either pattern or channel')
        self.channel = channel
        self.pattern = pattern
        self.sync = sync
        self.out = out

    def __call__(self, func):
        self.func = func
        listeners.append(self)
        return func

    def __repr__(self):
        return 'listener(' + ', '.join('%s=%r' % (k, v) for k, v in self.__dict__.items()) + ')'

    def get(self):
        d = dict()
        for attr in ('channel', 'pattern', 'sync', 'func', 'out'):
            d[attr] = getattr(self, attr) if hasattr(self, attr) else None
        return d
