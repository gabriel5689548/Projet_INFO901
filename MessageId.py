class MessageSendId():
    def __init__(self, payload, dest):
        self.dest = dest
        self.payload = payload
        
class MessageRegenerateId():
    def __init__(self, dest):
        self.dest = dest
        