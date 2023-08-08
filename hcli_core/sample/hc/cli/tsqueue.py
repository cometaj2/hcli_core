import threading
from collections import deque

# threadsafe queue
class TSQueue:
    def __init__(self):
        self.queue = deque()
        self.condition = threading.Condition()

    def put(self, item):
        with self.condition:
            self.queue.append(item)
            self.condition.notify()

    def get(self):
        with self.condition:
            while not self.queue:
                self.condition.wait()
            return self.queue.popleft()

    def peek(self):
        with self.condition:
            if not self.queue:
                return None
            return self.queue[0]

    def size(self):
        with self.condition:
            return len(self.queue)

    def empty(self):
        with self.condition:
            if len(self.queue) > 0:
                return True
            else:
                return False
