class Messages:
    def __init__(self):
        self.messages = []
        self.empty_message = '---'

    def append(self, message):
        self.messages.append(message)

    def last(self):
        if self.messages:
            return self.messages[-1]
        else:
            return self.empty_message