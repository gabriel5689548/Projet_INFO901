from threading import Lock, Thread

from time import sleep

from Com import Com

class Process(Thread):
    
    def __init__(self, name, nbProcess):
        Thread.__init__(self)

        self.com = Com(nbProcess, name)
        
        self.nbProcess = self.com.getNbProcess()

        self.alive = True
        self.start()
    

    def run(self):
        loop = 0
        sleep(2) # Permet de laisser le temps aux autres processus de s'initialiser avant la numérotation
        self.com.numerotation()
        if self.com.getMyId() == 0: # P0 envoie le jeton
            self.com.sendToken()
            
        while self.alive:
            if (self.com.getName() == "P0"):                
                self.com.sendToSync("salut 1 ! on se synchro ! dis le a 2 !" , 1)
                
                self.com.synchronize()
                self.com.requestSC()
                self.com.releaseSC()
                
                
                
            if (self.com.getMyId() == 1):
                self.com.receiveFromSynchrone()
                self.com.sendTo("salut 2 on se synchro !", 2)
                
                self.com.synchronize()
                self.com.requestSC()
                self.com.releaseSC()


                    
            if (self.com.getMyId() == 2):
                if not self.com.isMailboxEmpty():
                    print("P" + str(self.com.getMyId()) +" a un message dans sa boite : "+ self.com.getFirstMessage())
                    
                self.com.synchronize()
                self.com.requestSC()
                self.com.releaseSC()
                
            
            sleep(2)
            loop+=1

    def stop(self):
        self.alive = False

    def waitStopped(self):
        self.join()
    