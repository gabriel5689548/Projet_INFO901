from pyeventbus3.pyeventbus3 import *
from time import sleep
from Message import MessageDedie
from Message import MessageBroadCast
from Message import MessageBroadcastSynchrone
from Message import MessageDedieSynchrone
from Message import MessageDedieSynchroneReply
from MessageId import MessageSendId
from MessageId import MessageRegenerateId
from Synchronization import Synchronization
from Token import Token
from State import State
import threading
from random import randint


class Com():
    def __init__(self, nbProcess, name):
        """
        Initialisation de la classe de communication. 
        Définit le nombre de processus, le nom, l'état du jeton, l'horloge logique, et les mécanismes de synchronisation.
        """
        self.myId = -1
        self.nbProcess = nbProcess
        self.name = name

        self.clock = 0
        self.tokenState = State.NULL
        self.counterSynchro = nbProcess
        self.messageReceived = False
        self.semaphore = threading.Semaphore()
        self.mailbox = []
        
        self.generatedIds = []
        self.nbProcessIdToGenerate = nbProcess - 1
        
        PyBus.Instance().register(self, self)
        
    # Getters
    def getNbProcess(self):
        """
        Retourne le nombre de processus dans le système.
        """
        return self.nbProcess

    def getMyId(self):
        """
        Retourne l'identifiant du processus.
        """
        return self.myId
    
    def getClock(self):
        """
        Retourne l'horloge logique.
        """
        return self.clock