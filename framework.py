"""
Created on January 15, 2013

@author: Windward Studios, Inc. (www.windward.net).

No copyright claimed - do anything you want with this code.
"""

from __future__ import print_function
from __future__ import division

import sys, time, base64, traceback, threading
from xml.etree import ElementTree as ET

import tcpClient, myPlayerBrain, api
from debug import trap, printrap, bugprint

DEFAULT_ADDRESS = "127.0.0.1" #local machine


class Framework(object):
    def __init__(self, args):
        if len(args) >= 2:
            self._brain = myPlayerBrain.MyPlayerBrain(args[1])
        else:
            self._brain = myPlayerBrain.MyPlayerBrain()
        self.ipAddress = args[0] if len(args) >= 1 else DEFAULT_ADDRESS
        self.guid = None

        # this is used to make sure we don't have multiple threads updating the
        # Player/Passenger lists, sending back multiple orders, etc.
        self.lock = threading.Lock()

        print("Connecting to server '%s' for user: %r, school: %r" %
              (self.ipAddress, self._brain.name, myPlayerBrain.SCHOOL))

    def _run(self):
        print("starting...")

        self.client = tcpClient.TcpClient(self.ipAddress, self)
        self.client.start()
        self._connectToServer()

        #It's all messages to us now.
        print('enter "exit" to exit program')
        try:
            while True:
                line = raw_input()
                if line == 'exit':
                    break
        except EOFError:
            self.client.close() # exit on EOF
        finally:
            self.client.close()

    def statusMessage(self, message):
        trap()
        print(message)

    def incomingMessage(self, message):
        try:
            startTime = time.clock()
            # get the XML - we assume we always get a valid message from the server.
            xml = ET.XML(message)

            name = xml.tag
            if name == 'setup':
                print ("Received setup message")
                #TODO: logging
                players = api.units.playersFromXml(xml.find("players"))
                companies = api.map.companiesFromXml(xml.find("companies"))
                passengers = api.units.passengersFromXml(xml.find("passengers"), companies)
                map = api.map.Map(xml.find("map"), companies)
                self.guid = xml.attrib["my-guid"]
                me2 = [p for p in players if p.guid == self.guid][0]

                self._brain.setup(map, me2, players, companies, passengers, self.client)

                ###self.client.sendMessage(ET.tostring(doc))
            elif name == 'status':
                # may be here because re-started and got this message before
                # the re-send of setup
                if self.guid is None or len(self.guid) == 0:
                    trap()
                    return

                status = xml.attrib["status"]
                attr = xml.attrib["player-guid"]
                guid = attr if attr is not None else self.guid

                brain = self._brain

                if self.lock.acquire(False):
                    try:
                        api.units.updatePlayersFromXml(brain.players,
                                                       brain.passengers,
                                                       xml.find("players"))
                        api.units.updatePassengersFromXml(brain.passengers,
                                                          brain.companies,
                                                          xml.find("passengers"))
                        # update my path & pick-up
                        playerStatus = [p for p in brain.players
                                        if p.guid == guid][0]
                        elem = xml.find("path")
                        #bugprint('framework.py: path element ->', ET.tostring(elem))
                        if elem is not None and elem.text is not None:
                            path = [item.strip() for item in elem.text.split(';')
                                    if len(item.strip()) > 0]
                            del playerStatus.limo.path[:]
                            for stepOn in path:
                                pos = stepOn.index(',')
                                playerStatus.limo.path.append( (int(stepOn[:pos]),
                                                                int(stepOn[pos+1:])) )

                        elem = xml.find("pick-up")
                        #bugprint('framework.py: pick-up element ->', ET.tostring(elem))
                        if elem is not None and elem.text is not None:
                            names = [item.strip() for item in elem.text.split(';')
                                     if len(item) > 0]
                            playerStatus.pickup = [p for p in brain.passengers if p.name in names]

                        # pass in to generate new orders
                        brain.gameStatus(status, playerStatus, brain.players, brain.passengers)
                    #except Exception as e:
                    #    raise e
                    finally:
                        self.lock.release()
                else:
                    # failed to acquire the lock - we're throwing this message away.
                    trap()
                    return
            elif name == 'exit':
                print("Received exit message")
                #TODO: logging
                sys.exit(0)
            else:
                printrap("ERROR: bad message (XML) from server - root node %r" % name)

            turnTime = time.clock() - startTime
            prefix = '' if turnTime < .8 else "WARNING - "
            prefix = "!DANGER! - " if turnTime >= 1 else prefix
            print(prefix + "turn took %r seconds" % turnTime)
            #TODO: logging
        except Exception as e:
            traceback.print_exc()
            printrap("Error on incoming message.  Exception: %r" % e)

    def connectionLost(self, exception):
        print("Lost our connection! Exception: %r" % exception)
        client = self.client

        delay = .5
        while True:
            try:
                if client is not None:
                    client.close()
                client = self.client = tcpClient.TcpClient(self.ipAddress, self)
                client.start()

                self._connectToServer()
                print("Re-connected")
                return
            except Exception as e:
                print("Re-connection failed! Exception: %r" % e) # fix this
                time.sleep(delay)
                delay += .5

    def _connectToServer(self):
        root = ET.Element('join', {'name':     self._brain.name,
                                   'school':   myPlayerBrain.SCHOOL,
                                   'language': "Python"})
        avatar = self._brain.avatar
        if avatar is not None:
            av_el = ET.Element('avatar')
            av_el.text = base64.b64encode(avatar)
            root.append(av_el)
        self.client.sendMessage(ET.tostring(root))

def sendOrders(brain, order, path, pickup):
    """Used to communicate with the server. Do not change this method!"""
    xml = ET.Element(order)
    if len(path) > 0:
        brain.me.limo.path = path # update our saved Player to match new settings
        sb = [str(point[0]) + ',' + str(point[1]) + ';' for point in path]
        elem = ET.Element('path')
        elem.text = ''.join(sb)
        xml.append(elem)
    if len(pickup) > 0:
        brain.me.pickup = pickup # update our saved Player to match new settings
        sb = [psngr.name + ';' for psngr in pickup]
        elem = ET.Element('pick-up')
        elem.text = ''.join(sb)
        xml.append(elem)
    brain.client.sendMessage(ET.tostring(xml))

if __name__ == '__main__':
    printrap(sys.argv[0], breakOn=not sys.argv[0].endswith("framework.py"))
    framework = Framework(sys.argv[1:])
    framework._run()
