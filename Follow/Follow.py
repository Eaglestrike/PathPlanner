# -*- coding: utf-8 -*-
"""
Created on Tue Jan 16 21:18:18 2024

@author: degog
"""

import math

import Simulation.Drivebase as DB
from Code.Path import Path

def followImage(image, robotPos):
    imgPath = imageToPath(image)
    robotPath = followPath(imgPath, robotPos)
    return robotPath

def imageToPath(image):
    pass

def followPath(path, robotPos):
    robotPath = Path(mode = "linear")
    dt = 0.2
    t = path.getStartTime()
    maxT = path.getMaxTime()
    
    index = 0
    pose = path.poses[index][0]
    #pose = path.getPose(t)
    
    
    robotPosAng = robotPos.ang()
    while t <= maxT:
        targPose = path.getPose(t)
        
        d = targPose.pos - pose.pos
        
        #Finding new angle
        newAng = d.ang() - robotPosAng
        dAng = newAng - pose.ang
        dAng %= math.tau
        if dAng > math.pi:
            dAng -= math.tau
        elif dAng < -math.pi:
            dAng += math.tau
        newAng = pose.ang + dAng
        
        #Find new position
        newPose = DB.DrivePose(pose.pos.copy(), newAng)
        move = targPose.pos - newPose.getFieldPos(robotPos)
        newPose.pos += move
        #newPose.vel = (newPose.pos - pose.pos)/dt
        #newPose.angVel = (newAng - pose.ang)/dt
        
        pose = newPose
        
        robotPath.addPose(pose, t)
        #t += dt
        index += 1
        if index >= len(path):
            break
        t = path.poses[index][1]
    return robotPath
    