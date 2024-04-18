# -*- coding: utf-8 -*-
"""
Created on Fri Jan  5 12:55:01 2024

@author: degog
"""
import math

def sign(x):
    if x > 0:
        return 1.0
    elif x < 0:
        return -1.0
    else:
        return 0.0

class Pose():
    def __init__(self, pos:float, vel:float, acc:float):
        self.pos = pos
        self.vel = vel
        self.acc = acc
        
    def extrapolate(self, t):
        newVel = self.vel + self.acc * t
        newPos = self.pos + (newVel + self.vel)/2.0 * t
        return Pose(newPos, newVel, self.acc)
    
    def __str__(self):
        return "[pos: %.4f, vel: %.4f, acc: %.4f]" %(self.pos, self.vel, self.acc)
        
class TrapezoidalProfile():
    def __init__(self, maxV, maxA, initPose, finalPose):
        self.maxV = maxV
        self.maxA = maxA
        
        self.setTarget(initPose, finalPose)
        
    def getPose(self, t):
        if t > self.deaccTime:
            return self.finalPose.extrapolate(t - self.deaccTime)
        elif t > self.coastTime:
            return self.coastEnd.extrapolate(t - self.coastTime)
        elif t > self.accTime:
            return self.accEnd.extrapolate(t - self.accTime)
        elif t > 0.0:
            return self.startPose.extrapolate(t)
        else:
            return Pose(self.startPose.pos, 0.0, 0.0)
        
    def setTarget(self, currPose, finalPose):
        self.startPose = currPose
        if self.maxA == 0.0 or self.maxV == 0.0:
            return False
        
        self.finalPose = finalPose
        self.finalPose.acc = 0.0
        
        dx = self.finalPose.pos - self.startPose.pos
        dv = self.finalPose.vel - self.startPose.vel
        
        sVel = sign(dv)
        aVel = sVel * self.maxA
        tVel = 0.0
        if dv != 0.0:
            tVel = dv/aVel
        xVel = (self.finalPose.vel + self.startPose.vel)/2.0 * tVel
        
        xTpzd = dx - xVel
        sTpzd = sign(xTpzd)
        vTpzdM = sTpzd * self.maxV
        aTpzdM = sTpzd * self.maxA
        if sTpzd > 0.0:
            vTpzdI = max(self.finalPose.vel, self.startPose.vel)
        else:
            vTpzdI = min(self.finalPose.vel, self.startPose.vel)
        if aTpzdM != 0:
            xTpzdAcc = (vTpzdM*vTpzdM - vTpzdI*vTpzdI)/(2.0 * aTpzdM)
        else:
            xTpzdAcc = 0.0
        
        xCoast = xTpzd - 2.0*xTpzdAcc
        if xCoast * sTpzd > 0.0:
            tCoast = xCoast/vTpzdM
            vTpzd = vTpzdM
        else:
            tCoast = 0.0
            vTpzd = sTpzd * math.sqrt(vTpzdI*vTpzdI + aTpzdM*xTpzd)
            
        if aTpzdM != 0:
            tTpzdAcc = (vTpzd - vTpzdI)/aTpzdM
        else: 
            tTpzdAcc = 0.0
        
        self.startPose.acc = aTpzdM
        self.accTime = tTpzdAcc
        if sTpzd*sVel > 0.0:
            self.accTime += tVel
        xAccEnd = self.startPose.pos + (self.startPose.vel + vTpzd)/2.0 * self.accTime
        self.accEnd = Pose(xAccEnd, vTpzd, 0.0)
        self.coastTime = self.accTime + tCoast
        xCoastEnd = xAccEnd + vTpzd*tCoast
        self.coastEnd = Pose(xCoastEnd, vTpzd, -aTpzdM)
        self.deaccTime = 2.0*tTpzdAcc + tCoast + tVel
        return True
    
    def getDuration(self):
        return self.deaccTime
    
    def getDisplacement(self):
        return self.finalPose.pos - self.startPose.pos
        
        
    