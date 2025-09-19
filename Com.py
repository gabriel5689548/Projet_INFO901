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
        Retourne l'ID du processus actuel.
        """
        return self.myId
    
    def getName(self):
        """
        Retourne le nom du processus.
        """
        return self.name
        
    # Incrémentation de l'horloge
    def inc_clock(self):
        """
        Incrémente l'horloge logique du processus.
        """
        self.semaphore.acquire()
        self.clock += 1
        self.semaphore.release()
    
    # Incrémentation de l'horloge lors de la réception d'un message
    def inc_clock_receive(self, stamp):
        """
        Incrémente l'horloge logique du processus en fonction de l'horloge du message reçu.
        """
        self.semaphore.acquire()
        self.clock = max(self.clock, stamp) + 1
        self.semaphore.release()
      
    # Gestion de la boite aux lettres  
    def getFirstMessage(self):
        """
        Récupère le premier message de la boîte aux lettres du processus.
        """
        if (len(self.mailbox) > 0):
            return self.mailbox.pop(0).getPayload()
        else:
            return None
        
    def isMailboxEmpty(self):
        """
        Vérifie si la boîte aux lettres du processus est vide.
        """
        return len(self.mailbox) == 0

    # Réception de message dédié
    @subscribe(threadMode = Mode.PARALLEL, onEvent=MessageDedie)
    def onReceive(self, event):
        """
        Traite la réception d'un message dédié. 
        Si le message est destiné à ce processus, il met à jour l'horloge et le stocke dans la boîte aux lettres.
        """
        if (event.dest == self.myId):
            self.inc_clock_receive(event.getStamp())
            self.mailbox.append(event)

    # Envoi de message dédié
    def sendTo(self, message, dest):
        """
        Envoie un message dédié à un autre processus. Incrémente d'abord l'horloge du processus avant l'envoi.
        """
        self.inc_clock()
        m = MessageDedie(message,self.clock, dest)
        PyBus.Instance().post(m)
        
    
    # Réception de message broadcast
    @subscribe(threadMode = Mode.PARALLEL, onEvent=MessageBroadCast)
    def onBroadcast(self, event):
        """
        Traite la réception d'un message broadcast et met à jour l'horloge si le message vient d'un autre processus.
        """
        if (event.sender != self.myId):
            self.inc_clock_receive(event.getStamp())
            self.mailbox.append(event)

    # Envoi de message broadcast  
    def broadcast(self, contenu):
        """
        Envoie un message broadcast à tous les processus. Incrémente l'horloge avant l'envoi.
        """
        self.inc_clock()
        m = MessageBroadCast(contenu, self.clock, self.myId)
        PyBus.Instance().post(m)
        
    # Réception de jeton
    @subscribe(threadMode = Mode.PARALLEL, onEvent=Token)
    def onToken(self, event):
        """
        Traite la réception du jeton pour entrer ou sortir de la section critique.
        """
        if (event.to == self.myId):
            if (self.tokenState == State.REQUEST):
                self.tokenState = State.SC
                print("P" + str(self.myId) + " est en section critique")
                while (self.tokenState == State.SC):
                    sleep(1)
            
            self.tokenState = State.RELEASE
            self.sendToken()
    
    # Envoi de jeton     
    def sendToken(self):
        """
        Envoie le jeton au processus suivant.
        """
        t = Token((self.myId + 1) % self.nbProcess)
        PyBus.Instance().post(t)
    
    # Demande de section critique            
    def requestSC(self):
        """
        Demande d'entrée en section critique. Attend jusqu'à obtention du jeton.
        """
        self.tokenState = State.REQUEST
        while (self.tokenState == State.REQUEST):
            sleep(1)
    
    # Libération de section critique        
    def releaseSC(self):
        """
        Libère la section critique en changeant l'état du jeton.
        """
        self.tokenState = State.RELEASE
    
    # Réception de message de synchronisation
    @subscribe(threadMode = Mode.PARALLEL, onEvent=Synchronization)
    def onSynchronized(self, event):
        """
        Traite la réception d'un message de synchronisation et décrémente le compteur de synchronisation.
        """
        if (event.sender != self.myId):
            self.inc_clock_receive(event.stamp)
            self.counterSynchro -= 1
    
    # Synchronisation
    def synchronize(self):
        """
        Synchronise le processus avec les autres processus. Attend jusqu'à recevoir un message de chaque processus.
        """
        self.inc_clock()
        PyBus.Instance().post(Synchronization(self.clock, self.myId))
        while (self.counterSynchro > 1):  # 1 car on ne reçoit pas notre propre message
            sleep(1)
        print(self.getName() + " is synchronized")
        self.counterSynchro = self.nbProcess
        
    # Réception de message broadcast synchrone
    @subscribe(threadMode = Mode.PARALLEL, onEvent=MessageBroadcastSynchrone)
    def onBroadcastSynchrone(self, event):
        """
        Traite la réception d'un message broadcast synchrone et le stocke dans la boîte aux lettres.
        """
        if (event.sender != self.myId):
            self.inc_clock_receive(event.getStamp())
            self.mailbox.append(event)
            self.messageReceived = True
   
    # Envoi de message broadcast synchrone 
    def broadcastSynchrone(self, message, _from):
        """
        Envoie un message broadcast synchrone et attend la synchronisation avant de continuer.
        """
        if (self.myId == _from):
            self.inc_clock()
            m = MessageBroadcastSynchrone(message, self.clock, self.myId)
            PyBus.Instance().post(m)
            self.synchronize()
        else :
            while (self.messageReceived == False):
                sleep(1)
            self.synchronize()
            self.messageReceived = False
    
    # Réception de message dédié synchrone
    @subscribe(threadMode = Mode.PARALLEL, onEvent=MessageDedieSynchrone)
    def receiveMessageSynchrone(self, event):
        """
        Traite la réception d'un message dédié synchrone.
        """
        if (event.dest == self.myId):
            self.inc_clock_receive(event.getStamp())
            self.mailbox.append(event)
            self.messageReceived = True
    
    # Attente de réception de message synchrone
    def receiveFromSynchrone(self):
        """
        Attend la réception d'un message dédié synchrone. Une fois reçu, répond à l'expéditeur.
        """
        while (self.messageReceived == False):
            sleep(1)
        lastMessage = self.mailbox.pop()
        print(self.name + " a reçu : " + lastMessage.getPayload())
        m = MessageDedieSynchroneReply("", self.clock, lastMessage.sender)
        PyBus.Instance().post(m)
        self.messageReceived = False
    
    # Réception de réponse d'un message dédié synchrone
    @subscribe(threadMode = Mode.PARALLEL, onEvent=MessageDedieSynchroneReply)
    def receiveMessageSynchroneReply(self, event):
        """
        Traite la réception d'une réponse à un message dédié synchrone.
        """
        if (event.dest == self.myId):
            self.inc_clock_receive(event.getStamp())
            self.mailbox.append(event)
            self.messageReceived = True
        
    # Envoi de message dédié synchrone
    def sendToSync(self, message, dest):
        """
        Envoie un message dédié synchrone à un autre processus et attend une réponse.
        """
        self.inc_clock()
        m = MessageDedieSynchrone(message, self.clock, dest, self.myId)
        PyBus.Instance().post(m)
        while (self.messageReceived == False):
            sleep(1)
        self.messageReceived = False
    
    # Générer un ID aléatoire
    def generateId(self):
        """
        Génère un ID aléatoire pour ce processus. Le processus P0 reçoit toujours l'ID 0.
        """
        if (self.name == "P0"):
            self.myId = 0
        else :
            self.myId = randint(1, self.nbProcess - 1)
    
    # Numérotation des processus   
    def numerotation(self):
        """
        Procède à la numérotation des processus en générant des IDs.
        Si le processus est P0, il attend les IDs des autres processus.
        """
        self.generateId()
        if self.name == "P0":
            self.waitForIds()  # P0 attend que tous les processus envoient leurs IDs
        else:
            self.sendId(0)  # Envoyer l'ID à P0
    
    # Réception de l'ID des autres processus 
    @subscribe(threadMode = Mode.PARALLEL, onEvent=MessageSendId)
    def onReceiveId(self, event):
        """
        Traite la réception d'un ID envoyé par un autre processus et l'ajoute à la liste.
        """
        if (event.dest == self.myId):
            self.generatedIds.append(event.payload)            
    
    # Envoyer son ID à P0            
    def sendId(self, dest):
        """
        Envoie son ID au processus P0 pour la numérotation.
        """
        m = MessageSendId(self.myId, dest)
        PyBus.Instance().post(m)
        
    # Réception de la demande de régénération d'un ID
    @subscribe(threadMode=Mode.PARALLEL, onEvent=MessageRegenerateId)
    def onRegenerateId(self, event):
        """
        Régénère l'ID du processus si demandé par P0 en cas de doublon.
        """
        if event.dest == self.myId:
            print(f"{self.name} régénère son ID à la demande de P0.")
            self.generateId()
            self.sendId(0)  # Envoyer le nouvel ID à P0
    
    # Envoyer un messsage au processus pour régénérer l'id
    def requestRegenerateId(self, idToRegenerate):
        """
        Demande à un processus spécifique de régénérer son ID en cas de doublon.
        """
        m = MessageRegenerateId(idToRegenerate)
        PyBus.Instance().post(m)
        print("Demande envoyé à tous les processus pour régénérer l'ID " + str(idToRegenerate)) 
        
    # Attendre que tous les processus envoient leurs IDs (P0)
    def waitForIds(self):
        """
        P0 attend que tous les processus envoient leurs IDs pour vérifier les doublons.
        """
        while len(self.generatedIds) < self.nbProcessIdToGenerate:  # On attend que tous les processus (sauf P0) envoient un ID
            sleep(1)
        self.checkForDuplicateIds()
        
    # Vérifier les doublons et gérer la régénération
    def checkForDuplicateIds(self):
        """
        Vérifie si tous les IDs générés sont uniques. Si des doublons sont détectés, demande leur régénération.
        """
        uniqueIds = set(self.generatedIds)
        if len(uniqueIds) == len(self.generatedIds):
            print("Tous les IDs sont uniques! Aucun ID à régénérer.")
        else:
            print("Des doublons ont été détectés! Demande de régénération.")
            duplicateIds = [id for id in self.generatedIds if self.generatedIds.count(id) > 1]
            self.nbProcessIdToGenerate = len(duplicateIds)
            self.generatedIds = []  # Réinitialiser la liste et recommencer
            for id in set(duplicateIds):
                # On demande aux processus concernés de régénérer leur ID
                self.requestRegenerateId(id)
            self.waitForIds()  # Recommencer le processus d'attente d'IDs après la régénération
