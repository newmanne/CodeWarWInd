"""
Module simpleAStar: the sample pathfinding algorithm.  Start with this project
but write your own code as this is a very simplistic implementation of the AI.

There's a chance this *might* not be the world's worst A* implementation. It is
purposely simplistic to leave the teams the opportunity to improve greatly
upon it. (We were yelled at last year for making the sample A.I.s too good.)

Also there is (at least) one very subtle bug in the below code. It is very rarely hit.

Here's a good intro to A* search: http://www.policyalmanac.org/games/aStarTutorial.htm

Created on January 15, 2013

@author: Windward Studios, Inc. (www.windward.net).

No copyright claimed - do anything you want with this code.
"""

from __future__ import division
from __future__ import print_function

import time
from debug import trap, printrap, bugprint

OFFSETS = ( (-1, 0), (1, 0), (0, -1), (0, 1) )
DEAD_END = 10000
POINT_OFF_MAP = (-1, -1)

def calculatePath(gmap, start, end):
    """Calculate and return a path from start to end.

    This implementation is intentionally stupid and is NOT guaranteed in any
    way. Specifically, although it may, it is not guaranteed to:
        ->Return the shortest possible path
        ->Return a legal path
        ->Return in a reasonable amount of time
        ->Be free of bugs

    Use unmodified at your own risk.

    map -- The game map.
    start -- The tile units of the start point (inclusive).
    end -- The tile units of the end point (inclusive).

    """
    # should never happen but just to be sure
    if start == end:
        return [start]

    # nodes are points we have walked to
    nodes = {}
    # points we have in a trailPoint, but not yet evaluated
    notEvaluated = []

    tpOn = TrailPoint(start, end, 0)
    while True:
        nodes[tpOn.mapTile] = tpOn

        # get the neighbors
        tpClosest = None
        for ptOffset in OFFSETS:
            pointNeighbor = (tpOn.mapTile[0] + ptOffset[0], tpOn.mapTile[1] + ptOffset[1])
            square = gmap.squareOrDefault(pointNeighbor)
            # off the map or not a road/bus stop
            if square is None or (not square.isDriveable()):
                continue
            # already evaluated - add it in
            if pointNeighbor in nodes:
                tpAlreadyEvaluated = nodes[pointNeighbor]
                tpAlreadyEvaluated.cost = min(tpAlreadyEvaluated.cost, tpOn.cost+1)
                tpOn.neighbors.append(tpAlreadyEvaluated)
                continue

            # add this one in
            tpNeighbor = TrailPoint(pointNeighbor, end, tpOn.cost+1)
            tpOn.neighbors.append(tpNeighbor)
            # may already be in notEvaluated. If so remove it as this is a more
            # recent cost estimate.
            if tpNeighbor in notEvaluated:
                notEvaluated.remove(tpNeighbor)

            # we only assign to tpClosest if it is closer to the destination.
            # If it's further away, then we use notEvaluated below to find the
            # one closest to the dest that we ahve not walked yet.
            if tpClosest is None:
                if tpNeighbor.distance < tpOn.distance:
                    # new neighbor is closer - work from this next
                    tpClosest = tpNeighbor
                else:
                    # this is further away - put in the list to try if a
                    # better route is not found
                    notEvaluated.append(tpNeighbor)
            else:
                if tpClosest.distance <= tpNeighbor.distance:
                    # this is further away - put in the list to try if a
                    # better route is not found
                    notEvaluated.append(tpNeighbor)
                else:
                    # this is closer than tpOn and another neighbor - use it next.
                    notEvaluated.append(tpClosest)
                    tpClosest = tpNeighbor
        # re-calc based on neighbors
        tpOn.recalculateDistance(POINT_OFF_MAP, gmap.width)

        # if no closest, then get from notEvaluated. This is where it
        # guarantees that we are getting the shortest route - we go in here
        # if the above did not move a step closer. This may not either as
        # the best choice may be the neighbor we didn't go with above - but
        # we drop into this to find the closest based on what we know.
        if tpClosest is None:
            if len(notEvaluated) == 0:
                trap()
                break
            # we need the closest one as that's how we find the shortest path
            tpClosest = notEvaluated[0]
            for tpNotEval in notEvaluated:
                if tpNotEval.distance < tpClosest.distance:
                    tpClosest = tpNotEval
            notEvaluated.remove(tpClosest)

        # if we're at the end - we're done!
        if tpClosest.mapTile == end:
            tpClosest.neighbors.append(tpOn)
            nodes[tpClosest.mapTile] = tpClosest
            break

        # try this one next
        tpOn = tpClosest

    # create the return path - from end back to beginning
    tpOn = nodes[end]
    path = [tpOn.mapTile]
    while tpOn.mapTile != start:
        neighbors = tpOn.neighbors
        cost = tpOn.cost

        tpOn = min(neighbors, key=lambda n: n.cost)

        # we didn't get to the start.
        if tpOn.cost >= cost:
            trap()
            return path
        else:
            path.insert(0, tpOn.mapTile)

    return path

class TrailPoint(object):
    def __init__(self, point, end, cost):
        """A point in a car's path.

        mapTile -- The map tile (a 2-tuple) for this point in the trail.
        neighbors -- A list of the neighboring tiles (up to 4). If 0 then this
            point has been added as a neighbor but is in the notEvaluated list
            because it has not yet been tried.
        distance -- Estimate of the distance from mapTile to the end. Manhattan
            distance if have no neighbors, best neighbor.distance + 1 otherwise.
            This value is bad if it's along a trail that failed.

        """
        self.mapTile = point
        self.neighbors = []
        self.distance = abs(point[0] - end[0]) + abs(point[1] - end[1])
        self.cost = cost

    def recalculateDistance(self, mapTileCaller, remainingSteps):
        neighbors = self.neighbors
        trap(self.distance == 0)
        # if no neighbors then this is in notEvaluated and so can't recalculate.
        if len(neighbors) == 0:
            return

        shortestDistance = None
        # if just one neighbor, then it's a dead end
        if len(neighbors) == 1:
            shortestDistance = DEAD_END
        else:
            shortestDistance = min(neighbors, key=lambda n: n.distance).distance
            # it's 1+ lowest neighbor value (unless a dead end)
            if shortestDistance != DEAD_END:
                shortestDistance += 1

        # no change, no need to recalc neighbors
        if shortestDistance == self.distance:
            return
        # new value (could be shorter or longer)
        self.distance = shortestDistance
        # if gone too far, no more recalculate
        if remainingSteps < 0:
            return
        remainingSteps -= 1
        # need to tell our neighbors - except the one that called us
        newNeighbors = [n for n in neighbors if n.mapTile != mapTileCaller]
        for neighborOn in newNeighbors:
            neighborOn.recalculateDistance(self.mapTile, remainingSteps)
        # and we re-calc again because that could have changed our neighbors' values
        shortestDistance = min(neighbors, key=lambda n: n.distance).distance
        # it's 1+ lowest neighbor value (unless a dead end)
        if shortestDistance != DEAD_END:
            shortestDistance += 1
        self.distance = shortestDistance

    def __repr__(self):
        return ("TrailPoint<Map=%s, Cost=%s, Distance=%s, Neighbors=%s>" %
               (self.mapTile, self.cost, self.distance, len(self.neighbors)))

    def __hash__(self):
        return hash("TrailPoint at %r" % self.mapTile)

    def __eq__(self, other):
        if isinstance(other, TrailPoint) and other.mapTile == self.mapTile:
            return True
        else:
            return False