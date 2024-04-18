from Util.Vector import Vector
from Code.Path import Path
import Util.FileUtil
import Simulation.Drivebase as DB

import math

#directory = r"C:/Users/degog/Robotics/2024-RobotCode/src/main/deploy"
directory = "AutoGeneratedPaths"

def angDistance(a, b):
    angDiff = (b - a) % (2*math.pi)
    if angDiff > math.pi:
        angDiff -= 2*math.pi
    elif angDiff < -math.pi:
        angDiff += 2*math.pi
    return angDiff


speaker = Vector(0.0, 5.508)

start = {
    "LeftStart":    (Vector(0.722, 6.592), 4.146),
    "MidStart":     (Vector(1.317, 5.512), 3.141),
    "RightStart":   (Vector(0.787, 4.497), 2.172)
}

notes = {
    "LeftNear"      :Vector(2.858, 7.034),
    "MidNear"       :Vector(2.858, 5.570),
    "RightNear"     :Vector(2.858, 4.110),
    "LeftFar"       :Vector(8.267, 7.450),
    "MidLeftFar"    :Vector(8.267, 5.770),
    "MidFar"        :Vector(8.267, 4.122),
    "MidRightFar"   :Vector(8.267, 2.411),
    "RightFar"      :Vector(8.267, 0.732)
}
noteR = 0.08

score = {
    "LeftScore" :Vector(4.106, 6.787),
    "MidScore"  :Vector(4.168, 5.046),
    "RightScore":Vector(2.843, 2.458)
}

stage = [
    Vector(5.613, 5.434),
    Vector(5.577, 2.830),
    Vector(3.535, 4.080)
]
stageR = 0.45

shots = ["Near", "Score"]

robotR = 0.35

class FieldObject():
    def __init__(self, name:str, pos:Vector, rad:float):
        self.name = name
        self.pos = pos
        self.rad = rad


noteObjects = {name:FieldObject(name, note, noteR) for name, note in notes.items()}
stageObjects = {"Stage %d"%(i) : FieldObject("Stage %d"%(i), pos, stageR) for i, pos in enumerate(stage)}

class WayPoint():
    def __init__(self, pos:Vector, enterAng:float, enterAngTol:float, intakeDist:float):
        self.pos = pos
        self.enterAng = enterAng
        self.enterAngTol = enterAngTol
        self.intakeDist = intakeDist

    def checkEnterAng(self, ang) -> bool:
        return abs(angDistance(ang, self.enterAng)) < self.enterAngTol
    
    def copy(self):
        return WayPoint(self.pos, self.enterAng, self.enterAngTol, self.intakeDist)

angTol = 0.3
intakeDist = 0.35
lineupDist = 0.6
wayPoints = {}
for name, pos in list(notes.items()):
    if "Far" in name: #not a shot
        wayPoints[name] = WayPoint(pos, enterAng=math.pi, enterAngTol=math.pi, intakeDist = 0.0)
    else:
        ang = (speaker - pos).ang()
        if ang < 0:
            ang += math.tau
        wayPoints[name] = WayPoint(pos, enterAng=ang, enterAngTol=angTol, intakeDist = intakeDist)

for name, pos in list(score.items()):
    ang = (speaker - pos).ang()
    if ang < 0:
        ang += math.tau
    wayPoints[name] = WayPoint(pos, enterAng=ang, enterAngTol=angTol, intakeDist = 0.0)

for name, pose in start.items():
    wayPoints[name] = WayPoint(pose[0], enterAng=pose[1],enterAngTol=math.pi, intakeDist = 0.0)


def checkIntersection(path:Path, robotRad:float, objects:list[FieldObject], dt = 0.1):
    if dt <= 0.0:
        dt = 0.1
    
    maxT = path.getMaxTime()
    t = path.getStartTime()
    while t < maxT:
        robot = path.getPose(t)
        for o in objects:
            if (robot.pos - o.pos).mag() < (o.rad + robotRad):
                return (t, o)        
        t += dt
    return (-1, None)

kv = 0.0
def pathfind(path:Path, objects:list[FieldObject]):
    maxShift = 10
    for i in range(maxShift):
        t, obj = checkIntersection(path, robotR, objects)
        if obj == None:
            break
        
        pose = path.getPose(t)
        par = pose.vel.unit()
        perp = par.rotateCCW()

        dist = pose.pos - obj.pos

        newPose = pose.copy()
        if perp.dot(dist) <= 0.0:
            perp *= -1

        intersect = True
        dist = 0.0
        d = 0.05
        while intersect:
            newPose.pos += d*perp
            newPose.vel += kv*d*perp
            dist += d

            copy = path.copy(canvas = False)
            copy.addPose(newPose, t)
            res = checkIntersection(path, robotR, objects)
            intersect = res[1] is obj
                                 
            # for o in objects:
            #     if (newPose.pos - o.pos).mag() < (o.rad + robotR):
            #         intersect = True

            if dist > 1.5*(obj.rad + robotR): #failed resolving
                # objects.remove(obj)
                break

        path.addPose(newPose, t)

        path.regenerate()

    if i == (maxShift-1):
        print("failed")
    return path

def generatePath(start:WayPoint, stop:WayPoint, objects:list[FieldObject], maxV:float, maxA:float, pointTowards = False)->Path:
    path = Path(mode = "hermite")
    path.maxA = maxA
    path.maxV = maxV

    endDir = Vector.extend(stop.enterAng, 1.0)
    endDist = lineupDist - stop.intakeDist

    poses = [
        DB.DrivePose(start.pos + Vector.extend(start.enterAng, start.intakeDist), start.enterAng),
        DB.DrivePose(stop.pos + endDir * stop.intakeDist, stop.enterAng)
    ]

    if (stop.intakeDist != 0.0) and (not pointTowards):
        poses.insert(1, DB.DrivePose(stop.pos + endDir * lineupDist, stop.enterAng, vel = -((endDist * maxA)**0.5)*endDir))

    for pose in poses:
        for o in objects:
            if (o.pos - pose.pos).mag() < robotR + o.rad:
                objects.remove(o)

    for pose in poses:
        path.addPose(pose, path.getMaxTime() + 1.0)
    path.regenerate()

    path = pathfind(path, objects)

    if pointTowards:
        ang = (path.getPose(path.getMaxTime()-0.01).vel.ang() + math.pi)%math.tau
        if ang < 0:
            ang += math.tau
        path.poses[-1][0].ang = ang

    return path

sides3 = ["Left", "Mid", "Right"]
sides5 = ["Left", "MidLeft", "Mid", "MidRight", "Right"]

waypointType = {
    "Start" : sides3,
    "Near" : sides3,
    "Score" : sides3,
    "Far" : sides5
}

waypointMap = {
    "Start" : ["Near", "Far"],
    "Near" : ["Near", "Far"],
    "Score" : ["Near", "Far"],
    "Far" : ["Score", "Far"]
}

if __name__ == "__main__":
    for start, ends in waypointMap.items():
        for end in ends:
            for startType in waypointType[start]:
                startName = startType + start
                for endType in waypointType[end]:
                    endName = endType + end

                    if startName == endName:
                        continue

                    startWaypoint = wayPoints[startName]
                    endWaypoint = wayPoints[endName]
                    pointTowards = False

                    if ("Near" != start) and ("Start" != start) and ("Near" == end) and (endName != "RightNear"):
                        endWaypoint = endWaypoint.copy()
                        endWaypoint.intakeDist = 0.0
                        endWaypoint.enterAng = (endWaypoint.pos - startWaypoint.pos).ang()
                        if endWaypoint.enterAng < 0:
                            endWaypoint.enterAng += math.tau
                        pointTowards = True
                    
                    if (end == "Far"):
                        pointTowards = True
                    
                    objects = list(stageObjects.values())
                    for note, noteObject in noteObjects.items():
                        if note != startName and note != endName:
                            objects.append(noteObject)

                    path = generatePath(startWaypoint, endWaypoint, objects, 5.5, 5.5, pointTowards)
                    
                    filepath = directory + "/%s_to_%s.csv"%(startName, endName)
                    path.toDataframe().to_csv(filepath, index = False, lineterminator='\n')

                    print(filepath)