import queue as q


# Singleton Queue for sequential streaming jobs in a single process environment
class SQueue:
    instance = None
    queue = None

    def __new__(cls):
        if cls.instance is None:

            cls.instance = super().__new__(cls)
            cls.queue = q.Queue()

        return cls.instance

    def put(self, function):
        return self.queue.put(function)

    def get(self):
        return self.queue.get(self)

    def qsize(self):
        return self.queue.qsize()

    def empty(self):
        return self.queue.empty()

    def clear(self):
        self.queue.queue.clear()
