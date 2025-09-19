# 🚀 Middleware de Communication Distribuée (Python)

Ce projet implémente un **intergiciel (middleware)** en Python pour la gestion de la communication et de la synchronisation entre processus distribués, en s'appuyant sur un **Event Bus** (via `pyeventbus3`). Il respecte les contraintes d'un système distribué en implémentant l'**horloge de Lamport** et la gestion d'une **section critique distribuée** par jeton sur anneau.

## 👥 Auteurs

* ABRANTES ALFREDO Gabriel
* JBILOU Adam

---

## ✨ Fonctionnalités Implémentées

La classe centrale du projet est `Com`, le **communicateur**, qui gère l'ensemble des mécanismes de communication et de synchronisation pour chaque processus (`Process`).

### ⏰ Horloge Logique (Lamport)

* Implémentation de l'**horloge de Lamport** dans la classe `Com`.
* L'horloge est protégée par un **sémaphore** (`threading.Semaphore`).
* Elle est incrémentée lors de l'émission (`inc_clock()`) et mise à jour lors de la réception (`inc_clock_receive()`) des messages **utilisateurs**.
* Les messages système (comme le `Token` ou les messages d'ID) n'impactent pas l'horloge.

### ✉️ Communication Asynchrone

* Chaque processus dispose d'une **boîte aux lettres (B.a.L.)** (`self.mailbox`) pour les messages asynchrones.
* **`sendTo(message, dest)`**: Envoi d'un message dédié à la B.a.L. du processus de destination.
* **`broadcast(message)`**: Envoi d'un message à la B.a.L. de tous les autres processus.
* **`getFirstMessage()` / `isMailboxEmpty()`**: Méthodes pour consulter la B.a.L.

### 🔒 Section Critique Distribuée

* Utilisation de l'algorithme du **jeton sur anneau** pour l'accès à la section critique.
* Le jeton (`Token`) est un **message système** (n'impacte pas l'horloge).
* **`requestSC()`**: Bloque le processus jusqu'à l'obtention du jeton (`State.REQUEST`).
* **`releaseSC()`**: Libère la section critique (`State.RELEASE`).
* La gestion du jeton est traitée par des *threads* de l'Event Bus lors de la réception (`onToken`).

### 🔗 Synchronisation Collective

* **`synchronize()`**: Service bloquant qui attend que **tous** les processus aient invoqué cette méthode.
* Utilisation d'un compteur de synchronisation (`self.counterSynchro`) et de messages `Synchronization` pour coordonner les processus.

### 🌐 Numérotation Automatique

* Système de **numérotation unique et consécutive** des processus, allant de `0` à `nbProcess - 1`.
* Le processus `P0` reçoit l'ID `0`.
* Implémentation d'une vérification des IDs générés par les autres processus (`waitForIds()` et `checkForDuplicateIds()`).
* Le processus `P0` peut demander une **régénération d'ID** (`requestRegenerateId`) en cas de doublons (simulant une correction de numérotation).

### 🤝 Communication Synchrone (Bloquante)

* **`sendToSync(message, dest)`**: Envoie un message dédié synchrone et attend une réponse de l'expéditeur.
* **`receiveFromSynchrone()`**: Reçoit un message synchrone dédié et envoie un message de réponse (`MessageDedieSynchroneReply`) pour débloquer l'expéditeur.
* **`broadcastSynchrone(message, _from)`**:
    * Si le processus est `_from`, il envoie le message à tous et attend la synchronisation collective.
    * Sinon, il attend de recevoir le message de `_from` puis participe à la synchronisation.

---

## 🛠️ Structure du Projet

| Fichier | Description |
| :--- | :--- |
| `launcher.py` | Point d'entrée principal. Lance et gère les processus. |
| `Process.py` | Représente un processus distribué (hérite de `threading.Thread`). Contient le *main loop* du processus et interagit avec `Com`. |
| `Com.py` | La classe **Communicateur** (middleware). Contient l'horloge de Lamport, la boîte aux lettres, et toutes les méthodes de communication/synchronisation. |
| `Message.py` | Définition de la classe abstraite `Message` et de ses héritiers (Dédié, Broadcast, Synchrones, etc.). |
| `MessageId.py` | Classes de messages système pour la gestion et la régénération des IDs. |
| `Synchronization.py` | Classe de message système utilisé par la méthode `synchronize()`. |
| `Token.py` | Classe de message système représentant le jeton pour la section critique. |
| `State.py` | Énumération des états possibles du jeton (`NULL`, `REQUEST`, `SC`, `RELEASE`). |

---

## ▶️ Exécution

### Prérequis

* Python 3.x
* La bibliothèque `pyeventbus3` (peut nécessiter une installation via `pip`).

### Lancer le simulateur

Pour lancer la simulation avec 3 processus pendant 10 secondes :

```bash
python launcher.py