from model.server_change_state_thread import ServerChangeStateThread


class ServerChangeState(object):
    def __init__(self, smd, port):
        a = ServerChangeStateThread(smd, port)
        a.start()

