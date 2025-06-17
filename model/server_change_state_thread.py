import threading
from socket import socket


def listenClientChangeState(smd, port):
    Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # l'ip locale de l'ordinateur
    Host = '127.0.0.1'
    # choix d'un port
    Port = port

    # on bind notre socket
    Sock.bind((Host, Port))
    # On est a l'ecoute d'une seule et unique connexion :
    Sock.listen(1)

    while 1:

        # Le script se stoppe ici jusqu'a ce qu'il y ait connexion :
        client, adresse = Sock.accept()  # accepte les connexions de l'exterieur
        print("L'adresse", adresse, "vient de se connecter au serveur !")

        while 1:
            received = client.recv(1)
            if (len(received) == 0):
                break

            nbBitRead = ord(received)

            if nbBitRead == 0:
                print("end connection requested")
                break

            # on revoit n caracteres
            message = client.recv(nbBitRead)
            # si on ne recoit plus rien
            if not message:
                # on break la boucle (sinon les bips vont se repeter)
                break
            # affiche les donnees envoyees, suivi d'un bip sonore
            print("Entry into ", message)

            # Set message into State Machine Diagram
            smd._currentState = message
            # Refresh window
            smd._wnd.cmd_refresh()

        # ferme la connexion avec le client
        client.close()

        if nbBitRead == 0:
            print("end connection now")
            break



class ServerChangeStateThread(threading.Thread):
    def __init__(self, smd, port):
        threading.Thread.__init__(self)
        self._smd = smd
        self._port = port

    def run(self):
        print("Starting listenClientChangeState")
        listenClientChangeState(self._smd, self._port)
        print("End listenClientChangeState")


