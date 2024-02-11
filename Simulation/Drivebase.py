# -*- coding: utf-8 -*-
"""
Created on Sat Dec  2 20:58:11 2023

@author: degog

"""

import math

from Util.Vector import Vector

def angDistance(a, b):
    angDiff = (b - a) % (2*math.pi)
    if angDiff > math.pi:
        angDiff -= 2*math.pi
    elif angDiff < -math.pi:
        angDiff += 2*math.pi
    return angDiff

class Wheel():
    kResponse = 5.0
    kEMF = 2.1
    
    useDot = False
    kP = 6.5
    
    def __init__(self, ang, pos, drivepose, size, canvas = None, trails = False, vectors = False, layer = 2):
        self.ang = float(ang)
        self.vel = 0.0
        
        self.velTarget = Vector(0,0)
        
        self.fieldVel = Vector(0,0)
        
        self.pos = Vector(float(pos.x), float(pos.y))
        
        self.canvas = canvas
        self.trails = trails
        self.vectors = vectors
        
        if self.canvas is not None:
            self._createDrawing(drivepose, size, layer)
            self._draw(drivepose, 0.0)
    
    def setState(self, ang, vel, drivepose, t = None):
        self.ang = ang
        self.vel = vel
        self.fieldVel = Vector.extend(self.ang + drivepose.ang, self.vel)
        self._draw(drivepose, t)
        
    def setFieldVel(self, vel, drivepose, t = None):
        self.fieldVel = vel
        self.ang = vel.ang() - drivepose.ang
        self.vel = vel.mag()
        self._draw(drivepose, t)
    
    def setTarget(self, vel):
        self.velTarget = vel
    
    def calcVoltage(self, drivepose):
        if Wheel.useDot:
            driveVolts = (self.velTarget - self.fieldVel).dot(Vector.extend(self.ang + drivepose.ang, 1.0))
        else:
            driveVolts = self.velTarget.mag()
        if self.velTarget.mag() != 0.0:
            angDiff = angDistance(self.ang, self.velTarget.ang() - drivepose.ang)
            if angDiff > math.pi/2.0:
                if not Wheel.useDot:
                    driveVolts *= -1.0
                angDiff -= math.pi
            elif angDiff < -math.pi/2.0:
                if not Wheel.useDot:
                    driveVolts *= -1.0
                angDiff += math.pi
            turnVolts = Wheel.kP*angDiff
        else:
            turnVolts = 0.0
        driveVolts = max(-12, min(12, driveVolts))
        turnVolts = max(-12, min(12, turnVolts))
        return (driveVolts, turnVolts)
        
    def run(self, acc, drivepose, t, dt):
        driveVolts, turnVolts = self.calcVoltage(drivepose)
        dAng = turnVolts * dt
        self.ang += Wheel.kResponse*dAng
        direction = Vector.extend(self.ang + drivepose.ang, 1)
        
        externalAcc = acc.dot(direction)
        driveAcc = Wheel.kResponse*(driveVolts - Wheel.kEMF*self.vel)
        self.vel += (externalAcc + driveAcc)*dt
        
        self.fieldVel = direction * self.vel
        
        if self.canvas is not None:
            self._draw(drivepose, t)
    
    def _createDrawing(self, drivepose, size, layer):
        points = [
            Vector(-0.15, -0.05) * size,
            Vector(0.15, -0.05) * size,
            Vector(0.15, 0.05) * size,
            Vector(-0.15, 0.05) * size
            ]
        fieldPos = drivepose.getFieldPos(self.pos)
        self.canvasObject = self.canvas.addShape(fieldPos, self.ang, points, layer)
        if self.trails:
            self._createTrail(layer + 1)
        if self.vectors:
            self._createVector(fieldPos, layer + 1)
    
    def _createTrail(self, layer):
        self.trailObj = self.canvas.addPlotter([], "green", 4.0, layer = layer)
    
    def _createVector(self, fieldPos, layer):
        self.vectorObj = self.canvas.addVector(fieldPos, self.fieldVel*0.3, "black", layer = layer)
        
    def _draw(self, drivepose, t = None):
        fieldPos = drivepose.getFieldPos(self.pos)
        if self.trails and (t is not None):
            self.trailObj.addPoint(fieldPos, t)
        if self.vectors:
            self.vectorObj.setState(fieldPos,
                                    self.fieldVel*0.3)
        self.canvasObject.setState(fieldPos, self.ang + drivepose.ang)
    
    def getFieldVel(self):
        return self.fieldVel
    
    def getAngVel(self, drivepose):
        r = self.pos.mag()
        return (self.pos.rotate(drivepose.ang).cross(self.fieldVel))/(r*r)
    
    def clearTrails(self):
        if self.trails:
            self.trailObj.clear()
            
    def delete(self):
        if self.trails:
            self.trailObj.delete()
        if self.vectors:
            self.vectorObj.delete()
        if self.canvas is not None:
            self.canvasObject.delete()

class DrivePose():
    def __init__(self, pos, ang, vel = Vector(0,0), angVel = 0):
        self.pos = Vector(float(pos.x), float(pos.y))
        self.ang = float(ang)
        self.vel = Vector(float(vel.x), float(vel.y))
        self.angVel = float(angVel)
        
    def fromWheels(self, wheels, dt):
        vel = Vector(0,0)
        angVel = 0.0
        for w in wheels:
            vel += w.getFieldVel()
            angVel += w.getAngVel(self)
        vel /= len(wheels)
        angVel /= len(wheels)
        pos = self.pos + vel*dt
        ang = self.ang + angVel*dt
        return DrivePose(pos, ang, vel, angVel)
    
    def accelerate(self, acc, angAcc, dt):
        finalVel = self.vel + (acc * dt)
        self.pos += (finalVel + self.vel)/2.0 * dt
        self.vel = finalVel
        
        finalAngVel = self.angVel + angAcc * dt
        self.ang += (finalAngVel + self.angVel)/2.0 * dt
        self.angVel = finalAngVel
    
    def move(self, dt):
        self.pos += self.vel * dt
        self.ang += self.angVel * dt
        
    def getRobotPos(self, fieldPos):
        return (fieldPos - self.pos).rotate(-self.ang)
        
    def getFieldPos(self, posOnRobot):
        return posOnRobot.rotate(self.ang) + self.pos
    
    def getFieldVel(self, posOnRobot):
        return self.vel + self.angVel*posOnRobot.rotate(math.pi/2.0+self.ang)
    
    def copy(self):
        return DrivePose(self.pos.copy(), self.ang, self.vel.copy(), self.angVel)
    
    def interpolate(self, db2, t, span = 1.0):
        t1 = t/span
        t2 = (span - t)/span
        return DrivePose(
                self.pos*t2 + db2.pos*t1,
                self.ang*t2 + db2.ang*t1,
                (db2.pos - self.pos)/span,
                (db2.ang - self.ang)/span
            )
    
    def extrapolate(self, acc, angAcc, dt):
        finalVel = self.vel + (acc * dt)  
        finalAngVel = self.angVel + angAcc * dt
        return DrivePose( 
            self.pos + (finalVel + self.vel)/2.0 * dt,
            self.ang + (finalAngVel + self.angVel)/2.0 * dt,
            finalVel,
            finalAngVel
        )

class Drivebase():
    linFrict = 1.0
    angFrict = 1.0
    
    kLinP = 0.7
    kLinD = 0.07
    kLinV = 2.18
    kLinA = 0.55
    
    kAngP = 6.0
    kAngD = 0.5
    kAngV = 0.0
    
    def __init__(self, pose, size, canvas = None, trails = False, vectors = False, wheelTrails = False, wheelVecs = False, layer = 1):
        self.t = 0
        
        self.pose = pose.copy()
        self.targetVel = Vector(0,0)
        self.targetAngVel = 0.0
        self.size = size
        
        self.canvas = canvas
        self.trails = trails
        self.trailObj = None
        self.vectors = vectors
        
        self.shape = [Vector(self.size/2.0, self.size/2.0),
                      Vector(-self.size/2.0, self.size/2.0),
                      Vector(-self.size/2.0, -self.size/2.0),
                      Vector(self.size/2.0, -self.size/2.0)]
        
        self.wheels = [Wheel(0, p*0.8, self.pose, size, canvas, wheelTrails, wheelVecs, layer = layer+1) for p in self.shape]
        self.shape = [Vector(self.size/2.0, self.size/2.0),
                      Vector(-self.size/2.0, self.size/2.0),
                      Vector(-self.size/2.0, -self.size/2.0),
                      Vector(self.size/2.0, -self.size/2.0),
                      Vector(self.size/2.0, -self.size/4.0), #Cutout
                      Vector(self.size/3.0, -self.size/4.0),
                      Vector(self.size/3.0, self.size/4.0),
                      Vector(self.size/2.0, self.size/4.0)]
        
        if self.canvas is not None:
            self._createDrawing(layer)
            self._draw()
    
    def setPose(self, pose, t = None):
        self.pose = pose
        for w in self.wheels:
            wVel = self.pose.getFieldVel(w.pos)
            w.setFieldVel(wVel, self.pose, t)
        self._draw()
        
    def setTarget(self, vel, angVel):
        self.targetVel = vel
        self.targetAngVel = angVel
        for w in self.wheels:
            vel = self.targetVel + self.targetAngVel*(w.pos.rotate(self.pose.ang + math.pi/2))
            w.setTarget(vel)
            
    def setTargetPose(self, targPose, angWrapping = False):
        posError = targPose.pos - self.pose.pos
        velError = targPose.vel - self.pose.vel
        angError = targPose.ang - self.pose.ang
        if angWrapping:
            angError %= 2.0*math.pi
            if angError > math.pi:
                angError -= 2.0*math.pi
            if angError < -math.pi:
                angError += 2.0*math.pi
        angVelError = targPose.angVel - self.pose.angVel
        
        targetVel = (Drivebase.kLinP*posError + Drivebase.kLinD*velError + 
                     Drivebase.kLinV*targPose.vel)
        targetAngVel = (Drivebase.kAngP*angError + Drivebase.kAngD*angVelError + 
                        Drivebase.kAngV*targPose.angVel)
        if abs(targetAngVel) < 0.01:
            targetAngVel = 0.0
        
        self.setTarget(targetVel, targetAngVel)
        
    def run(self, dt):
        self.t += dt
        
        self.pose = self.pose.fromWheels(self.wheels, dt)
        
        friction = -Drivebase.linFrict*self.pose.vel
        angFriction = -Drivebase.angFrict*self.pose.angVel
        
        linAcc = friction
        angAcc = angFriction
        for w in self.wheels:
            acc = linAcc + (angAcc*w.pos.rotate(self.pose.ang+math.pi/2))
            w.run(acc, self.pose, self.t, dt)
        
        if self.canvas is not None:
            self._draw()
        
    def _createDrawing(self, layer):
        self.canvasObject = self.canvas.addShape(self.pose.pos, self.pose.ang, self.shape, layer = layer)
        self.canvasObject.setColor("blue")
        if self.trails:
            self._createTrail(layer + 1)
        if self.vectors:
            self._createVector(layer + 1)
        
    def _createTrail(self, layer):
        self.trailObj = self.canvas.addPlotter([], "green", 4.0, layer = layer)
    
    def _createVector(self, layer):
        self.vectorObj = self.canvas.addVector(self.pose.pos, self.pose.vel, "black", layer = layer)
    
    def _draw(self):
        if self.trails:
            self.trailObj.addPoint(self.pose.pos, self.t)
        if self.vectors:
            self.vectorObj.setState(self.pose.pos,
                                    self.pose.vel*0.3)
        self.canvasObject.setState(self.pose.pos, self.pose.ang)
        
    def getPos(self):
        return self.pose.pos
    
    def clearTrails(self):
        if self.trailObj is not None:
            self.trailObj.clear()
        for w in self.wheels:
            w.clearTrails()
            
            
    def delete(self):
        for w in self.wheels:
            w.delete()
        if self.trails:
            self.trailObj.delete()
        if self.vectors:
            self.vectorObj.delete()
        if self.canvasObject is not None:
            self.canvasObject.delete()
    
    