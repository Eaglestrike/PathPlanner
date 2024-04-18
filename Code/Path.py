# -*- coding: utf-8 -*-
"""
Created on Thu Dec 14 09:35:53 2023

@author: degog
"""

import pandas as pd
import math

import Simulation.Drivebase as DB

from Util.Vector import Vector
import Util.TrapezoidalProfile as TP

h00 = lambda t :  2 * t * t * t - 3 * t * t + 1
h10 = lambda t :  t * t * t - 2 * t * t + t
h01 = lambda t :  -2 * t * t * t + 3 * t * t
h11 = lambda t :  t * t * t - t * t
h00d = lambda t :  6 * t * t - 6 * t
h10d = lambda t :  3 * t * t - 4 * t + 1
h01d = lambda t :  6 * t - 6 * t * t
h11d = lambda t :  3 * t * t - 2 * t
h00dd = lambda t :  12 * t - 6
h10dd = lambda t :  6 * t - 4
h01dd = lambda t :  6 - 12 * t
h11dd = lambda t :  6 * t - 2

class Path():
    #Modes: linear, trapezoidal, hermite
    def __init__(self, mode = "linear", canvas = None, layer = 0, color = "blue"):
        self.poses = [] # List of (pose, time)
        
        self.segments = []
        
        self.mode = mode
        self.maxA = 1.0
        self.maxV = 1.0
        
        self.canvas = canvas
        self.canvasPaths = []
        self.color = color
        
        self.selectedIndex = -1
        self.selectedPos = None
        self.selectedVel = None
        self.selectedAng = None
        self.selectedObject = "pos"
        
        self.layer = layer
        
    def addPose(self, pose, time):
        if len(self) == 0:
            time = 0.0
            self.poses.append([pose, time])
        else:
            index = 0
            while self.poses[index][1] < time:
                index += 1
                if index >= len(self.poses):
                    break
            self.poses.insert(index, [pose, time])

        size = len(self)
        if size > 1:
            self.generatePath(size - 2)
        
    def getPose(self, time:float):
        if len(self.poses) == 0:
            return DB.DrivePose(Vector(0,0), 0)
        if time < self.poses[0][1]:
            return self.poses[0][0]
        for n, p in enumerate(self.poses[1:]): #Check pose of n+1
            pose1, t1 = self.poses[n]
            pose2, t2 = p
            length = t2-t1
            if time < t2:
                if self.mode == "linear":
                    return pose1.interpolate(pose2, time - t1, length)
                elif self.mode == "trapezoidal":
                    par = pose2.vel.unit()
                    perp = par.rotateCCW()
                    parPath, perpPath = self.segments[n]
                    t = time - t1
                    parPose = parPath.getPose(t)
                    perpPose = perpPath.getPose(t)
                    pos = pose1.pos + parPose.pos*par + perpPose.pos*perp
                    vel = parPose.vel*par + perpPose.vel*perp
                    dAng = pose2.ang - pose1.ang
                    ang = pose1.ang + dAng*(t/length)
                    return DB.DrivePose(pos, ang, vel, dAng/length)
                elif self.mode == "hermite":
                    tNew = (time - t1)/(t2 - t1)
                    ang = pose1.ang * h00(tNew) + pose1.angVel * h10(tNew) + pose2.ang * h01(tNew) + pose2.angVel * h11(tNew)
                    pos = pose1.pos * h00(tNew) + pose1.vel * h10(tNew) + pose2.pos * h01(tNew) + pose2.vel * h11(tNew)
                    angVel = pose1.ang * h00d(tNew) + pose1.angVel * h10d(tNew) + pose2.ang * h01d(tNew) + pose2.angVel * h11d(tNew)
                    vel = pose1.pos * h00d(tNew) + pose1.vel * h10d(tNew) + pose2.pos * h01d(tNew) + pose2.vel * h11d(tNew)
                    vel /= (t2 - t1)
                    angVel /= (t2 - t1)
                            
                    return DB.DrivePose(pos, ang, vel, angVel)
                else:
                    print("Wrong Mode")
        return self.poses[-1][0]
    
    def getStartTime(self):
        if len(self.poses) == 0:
            return 0
        return self.poses[0][1]
    
    def getMaxTime(self):
        if len(self.poses) == 0:
            return 0
        return self.poses[-1][1]
    
    #Updates the times of the waypoints
    def updateTimes(self, index:int):
        if self.mode == "trapezoidal":
            size = len(self)
            while index < size - 1:
                pose1, t1 = self.poses[index]
                parPath, perpPath = self.segments[index]
                self.poses[index+1][1] = t1 + max(parPath.getDuration(), perpPath.getDuration())
                index += 1
        elif self.mode == "hermite":
            size = len(self)
            while index < size - 1:
                pose1, t1 = self.poses[index]
                pose2, t2 = self.poses[index + 1]

                #Estimate time with a linear path
                dir = (pose2.pos - pose1.pos)
                dist = dir.mag()
                dir = dir.unit()

                p1 = TP.Pose(0.0, dir.dot(pose1.vel), 0.0)
                p2 = TP.Pose(dist, dir.dot(pose2.vel), 0.0)

                self.poses[index+1][1] = t1 + max(TP.TrapezoidalProfile(self.maxV, self.maxA, p1, p2).getDuration(), 0.01)
                index += 1
    
    def generatePath(self, index):
        while len(self.segments) < index + 1:
            self.segments.append(None)
        
        pose1, t1 = self.poses[index]
        pose2, t2 = self.poses[index+1]
        if self.mode == "linear":
            pass
        elif self.mode == "trapezoidal":
            par = pose2.vel.unit()
            perp = par.rotateCCW()
            dist = pose2.pos - pose1.pos
            initPosePar = TP.Pose(0, pose1.vel.dot(par), 0)
            finalPosePar = TP.Pose(dist.dot(par), pose2.vel.dot(par), 0)
            parPath = TP.TrapezoidalProfile(self.maxA, self.maxV, initPosePar, finalPosePar)
            initPosePerp = TP.Pose(0, pose1.vel.dot(perp), 0)
            finalPosePerp = TP.Pose(dist.dot(perp), pose2.vel.dot(perp), 0)
            perpPath = TP.TrapezoidalProfile(self.maxA, self.maxV, initPosePerp, finalPosePerp)
            self.segments[index] = (parPath, perpPath)
            self.updateTimes(index)
        elif self.mode == "hermite":
            self.updateTimes(0)
            
        if self.canvas is not None:
            self._drawPath(index)
    
    def _drawPath(self, index):
        while len(self.canvasPaths) < index + 1:
            self.canvasPaths.append(None)
        
        pose1, t1 = self.poses[index]
        pose2, t2 = self.poses[index+1]
        
        if self.mode == "linear":
            points = [pose1.pos, pose2.pos]
        else:
            t = 0
            dt = t2 - t1
            points = []
            while t < dt:
                pose = self.getPose(t + t1)
                points.append(pose.pos)
                t += 0.1
            points.append(self.getPose(t2).pos)
        
        if self.canvasPaths[index] is None:
            self.canvasPaths[index] = self.canvas.addPlotter(points, self.color, layer = self.layer)
        else:
            self.canvasPaths[index].setPoints(points)
        
    def clear(self):
        self.poses.clear()
        
        for i in self.canvasPaths:
            i.delete()
        self.canvasPaths.clear()
        
        self.selectedIndex = -1
        self._updateSelect()
    
    #Updates the canvas
    def _updateSegment(self, index):
        pose, t = self.poses[index]
        if self.mode == "linear":
            if index != 0:    
                self.canvasPaths[index-1].editPoint(1, pose.pos)
            if index != len(self) -1:
                self.canvasPaths[index].editPoint(0, pose.pos)
        else:
            if index != 0:   
                self.generatePath(index-1)
            if index != len(self) -1:
                self.generatePath(index)
            
    
    def _updateSelect(self):
        if self.selectedIndex < 0:
            if self.selectedPos is not None:
                self.selectedPos.delete()
                self.selectedVel.delete()
                self.selectedAng.delete()
                self.selectedPos = None
                self.selectedVel = None
                self.selectedVel = None
            return
        
        pose, t = self.poses[self.selectedIndex]
        if self.selectedPos is None:
            self.selectedPos = self.canvas.addPoint(pose.pos, "green", layer = self.layer + 1)
            self.selectedVel = self.canvas.addVector(pose.pos, pose.vel*0.3, "green", layer = self.layer + 1)
            self.selectedAng = self.canvas.addPoint(pose.pos + Vector.extend(pose.ang, 0.5), "green", layer = self.layer + 1)
        else:
            self.selectedPos.setPos(pose.pos)
            self.selectedVel.setState(pose.pos, pose.vel*0.3)
            self.selectedAng.setPos(pose.pos + Vector.extend(pose.ang, 0.5))
        self._updateSegment(self.selectedIndex)
            
    selectDist = 0.5
    def selectPoint(self, pos):
        #Check selecting ang, pos, or vel
        minDist = float("inf")
        if self.selectedIndex >= 0:
            pose, t = self.poses[self.selectedIndex]
            items = [
                ("pos", pose.pos),
                ("vel", pose.pos + pose.vel*0.3), #Velocity vector scaling for display
                ("ang", pose.pos + Vector.extend(pose.ang, 0.5))
            ]
            select = None
            for selectType, point in items:
                dist = (point - pos).mag()
                if dist < minDist and dist < Path.selectDist:
                    minDist = dist
                    select = selectType
            if select is not None:
                self.selectedObject = select
                return
            
        #Find closest point on path
        closest = -1
        for n, p in enumerate(self.poses):
            pose, t = p
            dist = (pose.pos - pos).mag()
            if dist < minDist and dist < Path.selectDist:
                closest = n
                minDist = dist
                
        self.selectedIndex = closest
        self._updateSelect()
    
    def shiftSelect(self, num):
        nextIndex = self.selectedIndex + num
        if nextIndex < 0 or nextIndex > len(self)-1:
            return
        self.selectedIndex = nextIndex
        self._updateSelect()
        
    def dragged(self, pos):
        if self.selectedIndex < 0:
            return
        if self.selectedObject == "pos":
            self.poses[self.selectedIndex][0].pos = pos
        elif self.selectedObject == "vel":
            self.poses[self.selectedIndex][0].vel = (pos - self.poses[self.selectedIndex][0].pos)/0.3 #Scaling factor
        elif self.selectedObject == "ang":
            ang = (pos - self.poses[self.selectedIndex][0].pos).ang()
            diff = (ang - self.poses[self.selectedIndex][0].ang)%math.tau
            if diff > math.pi:
                diff -= math.tau
            self.poses[self.selectedIndex][0].ang += diff
        self._updateSelect()
    
    def setCanvas(self, canvas, layer = 0):
        self.canvas = canvas
        tempPoses = self.poses.copy()
        self.clear()
        for path, t in tempPoses:
            self.addPose(path, t)
    
    def setMode(self, mode):
        if mode not in ("linear", "trapzoidal", "hermite"):
            return
    
    def toDataframe(self):
        data = []
        for pose, time in self.poses:
            poseData = dict()
            poseData["x"] = pose.pos.x
            poseData["y"] = pose.pos.y
            poseData["vx"] = pose.vel.x
            poseData["vy"] = pose.vel.y
            poseData["ang"] = pose.ang
            poseData["angVel"] = pose.angVel
            poseData["t"] = time
            data.append(poseData)
        return pd.DataFrame(data)
    
    def setDataFrame(self, dataFrame):
        self.clear()
        self.addDataFrame(dataFrame)
    
    def addDataFrame(self, dataFrame:pd.DataFrame):
        if len(self) == 0:
            t = 0
        else:
            t = self.poses[-1][1] + 0.0001
        for index, row in dataFrame.iterrows():
            pos = Vector(row["x"], row["y"])
            vel = Vector(row["vx"], row["vy"])
            pose = DB.DrivePose(pos, row["ang"], vel, row["angVel"])
            self.poses.append([pose, row["t"] + t])
        self.regenerate()
    
    def regenerate(self):
        self.selectedIndex = -1
        self._updateSelect()
        for i in range(len(self)-1):
            self.generatePath(i)

    def copy(self, canvas = True):
        if canvas:
            path = Path(self.mode, self.canvas, self.layer, self.color)
        else:
            path = Path(self.mode)
        for pose, t in self.poses:
            path.addPose(pose.copy(), t)
        path.regenerate()
        return path
        
    def scale(self, k):
        for n, pose in enumerate(self.poses):
            dPose, t = pose
            dPose.vel *= k
            dPose.pos *= k
            self.poses[n][1] *= k
        self.regenerate()
        
    def zero(self, pos = Vector(0,0)):
        if len(self) == 0:
            return
        diff = pos - self.poses[0][0].pos.copy() 
        for pose, t in self.poses:
            pose.pos += diff
        self.regenerate()
        
    def __len__(self):
        return len(self.poses)
        