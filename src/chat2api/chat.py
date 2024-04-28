from abc import abstractmethod


class ChatServer:

    @abstractmethod
    def answer_stream(self, *args, **kwargs):
        pass
