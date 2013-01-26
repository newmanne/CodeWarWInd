"""
Module units: classes, functions and constants for working with players,
passengers, and their tokens.

Created on January 15, 2013

@author: Windward Studios, Inc. (www.windward.net).

No copyright claimed - do anything you want with this code.
"""

from xml.etree import ElementTree as ET
import debug

STATUS = ("UPDATE", "NO_PATH", "PASSENGER_ABANDONED", "PASSENGER_DELIVERED",
          "PASSENGER_DELIVERED_AND_PICKED_UP", "PASSENGER_REFUSED",
          "PASSENGER_PICKED_UP", "PASSENGER_NO_ACTION")
"""
Current status of the player:
UPDATE: Called ever N ticks to update the AI with the game status.
NO_PATH: The car has no path.
PASSENGER_ABANDONED: The passenger was abandoned, no passenger was picked up.
PASSENGER_DELIVERED: The passenger was delivered, no passenger was picked up.
PASSENGER_DELIVERED_AND_PICKED_UP: The passenger was delivered or abandoned, a new passenger was picked up.
PASSENGER_REFUSED: The passenger refused to exit at the bus stop because an enemy was there.
PASSENGER_PICKED_UP: A passenger was picked up. There was no passenger to deliver.
PASSENGER_NO_ACTION: At a bus stop, nothing happened (no drop off, no pick up).

"""


class Player(object):
    """Class for representing a player in the game."""
    
    def __init__(self, element, pickup=[], passes=[], score=0):
        """Create a player instance from the given XML Element.

        Initialize the following instance variables:
        guid -- A unique string identifier for this player. This string will remain
            constant throughout the game (while the Player objects passed will change
            on every call).
        name -- The name of this player.
        pickup -- List of who to pick up at the next bus stop. Can be empty and
            can also only list people not at the next bus stop. This may be
            wrong after a pick-up occurs as all we get is a count. This is
            updated with the most recent list sent to the server.
        passengersDelivered -- The passengers delivered so far (this game).
        limo -- The player's limo.
        score -- The score for this player (this game, not across all games so far).

        """
        if isinstance(element, basestring):
            element = ET.XML(element)
        self.guid = element.get('guid')
        self.name = element.get('name')
        self.limo = Limo( (int(element.get('limo-x')), int(element.get('limo-y'))),
                           int(element.get('limo-angle')))
        self.pickup = pickup
        self.passengersDelivered = passes
        self.score = score

    def __repr__(self):
        return ("Player('" +
                '<player guid="%s" name=%r limo-x="%r" limo-y="%r" limo-angle="%r">' %
                (self.guid, self.name, self.limo.tilePosition[0], self.limo.tilePosition[1], self.limo.angle) +
                "', %r, %r, %r)" % (self.pickup, self.passengersDelivered, self.score))

    def __str__(self):
        return "%s; numDelivered:%r" % (self.name, len(self.passengersDelivered))

    def __eq__(self, other):
        if instanceof(other, Player) and other.guid == self.guid:
            return True
        else:
            return False

    def __hash__(self):
        return hash('Player %s (%r)' % (self.name, self.guid))

class Limo(object):
    """A player's limo - holds a single passenger."""
    def __init__(self, tilePosition, angle, path=[], passenger=None):
        """tilePosition -- The location in tile units of the center of the vehicle.
        angle -- the angle this unit is facing (an int from 0 to 359; 0 is
            North and 90 is East.
        path -- Only set for the AI's own limo - the number of tiles
            remaining in the limo's path. This may be wrong after movement
            as all we get is a count. This is updated witht the most recent
            list sent to the server.
        passenger -- The passenger in this limo. None if there is no passenger.

        """
        self.tilePosition = tilePosition
        self.angle = angle
        self.path = path
        self.passenger = passenger

    def __str__(self):
        if self.passenger is not None:
            return ("%s:%s; Passenger:%s; Dest:%s; PathLength:%s" %
                    (self.tilePosition, self.angle, self.passenger.name,
                    self.passenger.destination, len(self.path)))
        else:
            return "%s:%s; Passenger:{none}" % (self.tilePosition, self.angle)

class Passenger(object):
    """A company CEO."""
    def __init__(self, element, companies):
        """Create a passenger from XML and a list of Company objects.

        name -- The name of this passenger.
        pointsDelivered -- The number of points a player get for delivering this passenger.
        car -- The limo the passenger is currently in. None if they are not in a limo.
        lobby -- The bus stop the passenger is currently waiting in. None if they
            are in a limo or if they have arrived at their final destination.
        destination -- The company the passenger wishes to go to next. This is
            valid both at a bus stop and in a car. It is None of they have been
            delivered to their final destination.
        route -- The remaining companies the passenger wishes to go to after
            destination, in order. This does not include their current destination.
        enemies -- List of other Passenger objects. If any of them are at a bus
            stop, this passenger will not exit the limo at that stop. If a
            passenger at the bus stop has this passenger as an enemy, this
            passenger can still exit the car.

        """
        self.name = element.get('name')
        self.pointsDelivered = int(element.get('points-delivered'))
        lobby = element.get('lobby')
        self.lobby = ([c for c in companies if c.name == lobby][0]
                      if lobby is not None else None)
        dest = element.get('destination')
        self.destination = ([c for c in companies if c.name == dest][0]
                            if dest is not None else None)
        route = []
        for routeElement in element.findall('route'):
            debug.trap()
            route.append([c for c in companies if c.name == routeElement.text][0])
        self.route = route
        self.enemies = []
        self.car = None

    def __repr__(self):
        return self.name

def playersFromXml (element):
    """Called on setup to create initial list of players."""
    return [Player(p) for p in element.findall('player')]

def updatePlayersFromXml (players, passengers, element):
    """Update a list of Player objects with passengers from the given XML."""
    for playerElement in element.findall('player'):
        player = [p for p in players if p.guid == playerElement.get('guid')][0]
        player.score = float(playerElement.get('score'))
        # car location
        player.limo.tilePosition = ( int(playerElement.get('limo-x')),
                                     int(playerElement.get('limo-y')) )
        player.limo.angle = int(playerElement.get('limo-angle'))
        # see if we now have a passenger
        psgrName = playerElement.get('passenger')
        if psgrName is not None:
            passenger = [p for p in passengers if p.name == psgrName][0]
            player.limo.passenger = passenger
            passenger.car = player.limo
        else:
            player.limo.passenger = None
        # add most recent delivery if this is the first time we're told.
        psgrName = element.get('last-delivered')
        if psgrName is not None:
            passenger = [p for p in passengers if p.name == psgrName][0]
            if passenger not in player.passengersDelivered:
                player.passengersDelivered.append(passenger)

def passengersFromXml (element, companies):
    elements = element.findall('passenger')
    passengers = [Passenger(psgr, companies) for psgr in elements]
    # need to now assign enemies - needed all Passenger objects created first
    for elemOn in elements:
        psgr = [p for p in passengers if p.name == elemOn.get('name')][0]
        psgr.enemies = [filter(lambda p: p.name == e.text, passengers)[0]
                        for e in elemOn.findall('enemy')]
    # set if they're in a lobby
    for psgr in passengers:
        if psgr.lobby is not None:
            company = [c for c in companies if c == psgr.lobby][0]
            company.passengers.append(psgr)
    return passengers

def updatePassengersFromXml (passengers, companies, element):
    for psgrElement in element.findall('passenger'):
        #debug.bugprint('updatePassengers XML:', ET.tostring(psgrElement))
        #debug.bugprint('  passengers: ' + str(passengers))
        passenger = [p for p in passengers if p.name == psgrElement.get('name')][0]
        dest = psgrElement.get('destination')
        if dest is not None:
            passenger.destination = [c for c in companies if c.name == dest][0]
            # remove from the route
            if passenger.destination in passenger.route:
                passenger.route.remove(passenger.destination)
        # set props based on waiting, travelling, done
        switch = psgrElement.get('status')
        if   switch == "lobby":
            passenger.lobby = [c for c in companies if c.name == psgrElement.get('lobby')][0]
            passenger.car = None
        elif switch == "travelling":
            passenger.lobby = None
            # passenger.car set in Player update
        elif switch == "done":
            debug.trap()
            passenger.destination = None
            passenger.lobby = None
            passenger.car = None
        else:
            raise TypeError("Invalid passenger status in XML: %r" % switch)