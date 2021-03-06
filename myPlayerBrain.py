"""
Module myPlayerBrain: the sample Python AI.  Start with this project but write
your own code as this is a very simplistic implementation of the AI.

Created on January 15, 2013

@author: Windward Studios, Inc. (www.windward.net).

No copyright claimed - do anything you want with this code.
"""
from __future__ import division

import random
import simpleAStar
from framework import sendOrders
from api import units, map
from debug import printrap



from xml.etree import ElementTree as ET
import traceback
import __builtin__

NAME = "Tejas, Zongyi, Cheng, Neil Python"
SCHOOL = "Uoft"

class MyPlayerBrain(object):
    """The Python AI class.  This class must have the methods setup and gameStatus."""
    def __init__(self, name=NAME):
        self.name = name #The name of the player.
        
        #The player's avatar (looks in the same directory that this module is in).
        #Must be a 32 x 32 PNG file.
        try:
            avatar = open("MyAvatar.png", "rb")
            avatar_str = b''
            for line in avatar:
                avatar_str += line
            avatar = avatar_str
        except IOError:
            avatar = None # avatar is optional
        self.avatar = avatar
    
    def setup(self, gMap, me, allPlayers, companies, passengers, client):
        """
        Called at the start of the game; initializes instance variables.

        gMap -- The game map.
        me -- Your Player object.
        allPlayers -- List of all Player objects (including you).
        companies -- The companies on the map.
        passengers -- The passengers that need a lift.
        client -- TcpClient to use to send orders to the server.
        
        """
        self.gameMap = gMap
        self.players = allPlayers
        self.me = me
        self.companies = companies
        self.passengers = passengers
        self.client = client

        self.pickup = pickup = self.allPickups(me, passengers, self.players)

        # get the path from where we are to the dest.
        path = self.calculatePathPlus1(me, pickup[0].lobby.busStop)
        sendOrders(self, "ready", path, pickup)

    def gameStatus(self, status, playerStatus, players, passengers):
        """
        Called to send an update message to this A.I.  We do NOT have to send a response.

        status -- The status message.
        playerStatus -- The player this status is about. THIS MAY NOT BE YOU.
        players -- The status of all players.
        passengers -- The status of all passengers.

        """

        # bugbug - Framework.cs updates the object's in this object's Players,
        # Passengers, and Companies lists. This works fine as long as this app
        # is single threaded. However, if you create worker thread(s) or
        # respond to multiple status messages simultaneously then you need to
        # split these out and synchronize access to the saved list objects.

        try:
            # bugbug - we return if not us because the below code is only for
            # when we need a new path or our limo hits a bus stop. If you want
            # to act on other players arriving at bus stops, you need to
            # remove this. But make sure you use self.me, not playerStatus for
            # the Player you are updating (particularly to determine what tile
            # to start your path from).
            if playerStatus != self.me:
                return

            ptDest = None
            pickup = []
            if    status == "UPDATE":
                return
            elif ((status == "PASSENGER_NO_ACTION" or
                  status == "NO_PATH") and playerStatus == self.me):
                if playerStatus.limo.passenger is None:
                    pickup = self.allPickups(self.me, passengers, players)
                    ptDest = pickup[0].lobby.busStop
                else:
                    ptDest = playerStatus.limo.passenger.destination.busStop
            elif (status == "PASSENGER_DELIVERED" or
                  status == "PASSENGER_ABANDONED"):
                pickup = self.allPickups(self.me, passengers, players)
                ptDest = pickup[0].lobby.busStop
            elif  status == "PASSENGER_REFUSED":
                pickup = self.allPickups(self.me, passengers, players)
                ptDest = pickup[0].lobby
            elif (status == "PASSENGER_DELIVERED_AND_PICKED_UP" or
                  status == "PASSENGER_PICKED_UP"):
                pickup = self.allPickups(self.me, passengers, players)
                ptDest = self.me.limo.passenger.destination.busStop
            else:
                raise TypeError("unknown status %r", status)

            # get the path from where we are to the dest.
            path = self.calculatePathPlus1(self.me, ptDest)
            
            sendOrders(self, "move", path, pickup)
        except Exception as e:
            traceback.print_exc()
            printrap ("somefin' bad, foo'!")
            raise e

    def calculatePathPlus1 (self, me, ptDest):
        path = simpleAStar.calculatePath(self.gameMap, me.limo.tilePosition, ptDest)
        # add in leaving the bus stop so it has orders while we get the message
        # saying it got there and are deciding what to do next.
        if len(path) > 1:
            path.append(path[-2])
        return path
    
    def easierForYou(self, passenger, me, otherAi):
        toPassenger = len(simpleAStar.calculatePath(self.gameMap, me.limo.tilePosition, passenger.lobby.busStop))
        otherAiToPassenger = len(simpleAStar.calculatePath(self.gameMap, otherAi.limo.tilePosition, passenger.lobby.busStop))
        return True if toPassenger < otherAiToPassenger else False
    
    def allPickups (self, me, passengers, players):
            def distanceFromUs(p):
                toPassenger = len(simpleAStar.calculatePath(self.gameMap, me.limo.tilePosition, p.lobby.busStop))
                toDest = len(simpleAStar.calculatePath(self.gameMap, p.lobby.busStop, p.destination.busStop))
                return toPassenger + toDest
            def keyFunc(p):
                return (100*p.pointsDelivered)/distanceFromUs(p)
            
            pickup = [p for p in passengers if (not p in me.passengersDelivered and
                                                p != me.limo.passenger and
                                                p.car is None and
                                                p.lobby is not None and p.destination is not None)]
            tempPickup = filter(lambda x: len([y for y in x.enemies if y in x.destination.passengers]) ==0, pickup)
            if len(tempPickup) > 0:
                pickup = tempPickup
            """Not Sure about this Part Yet"""
#             for player in players:
#                 tempPickup = filter(lambda x: self.easierForYou(x, me, player), pickup)
#                 if len(tempPickup) > 0:
#                     pickup = tempPickup
            values = __builtin__.map(lambda x: (x, keyFunc(x)), pickup)
            values = sorted(values, key=lambda x: x[1], reverse=True)
            pickup = __builtin__.map(lambda x: x[0], values)
            print values                    
            return pickup
        
    def sortPickUps(self, me, passengers, players):
        pass
            