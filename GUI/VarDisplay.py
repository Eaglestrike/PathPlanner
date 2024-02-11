# -*- coding: utf-8 -*-
"""
Created on Mon May  1 23:33:21 2023

@author: degog
"""

import tkinter as tk

class VarDisplay(tk.Frame):
    displays = []
    def __init__(self, master, obj, varName, name = None, edit = False):
        tk.Frame.__init__(self, master)
        self.configure(relief = "solid", borderwidth = 2)
        
        self.obj = obj
        self.varName = varName.split(".")
        
        self.edit = edit
        
        self.prevVal = None
        self.updated = False
        
        #Name of variable
        self.textVar = tk.StringVar()
        if name == None:
            tk.Label(self, text = "%s"%(varName)).pack(side = 'left', padx = 10)
        else:
            tk.Label(self, text = name).pack(side = 'left', padx = 10)
        #Value
        if edit:
            entry = tk.Entry(self, textvariable = self.textVar)
            entry.bind("<KeyRelease>",self.updateVar)
            entry.pack(side = 'right')
        if not edit:
            label = tk.Label(self, textvariable = self.textVar)
            label.pack(side = 'right')
            label.config({"background" : "Light Gray", "width" : "15"})
            
        VarDisplay.displays.append(self)
        self.updateSelf()
        self.pack(side = "top", fill = "x", expand=True)
    
    def getVal(self):
        val = self.obj
        for var in self.varName:
            var = var.replace("]", "").split("[")
            val = getattr(val, var[0])
            for index in var[1:]:
                val = val[int(index)]
        if callable(val):
            val = val()
        return val
    
    def valToString(self, val):
        valType = type(val)
        if valType == float:
            return ("%.6f" %(val))
        elif valType == list:
            return "["+(",".join([self.valToString(v) for v in val]))+"]"
        else:
            return str(val)
        
    def stringToVal(self, string, valType):
        if valType == float:
            if len(string) == 0:
                return None
            test = string
            if test[0] == "-":
                test = test[1:]
            if test.replace(".", "", 1).isnumeric():
                return float(string)
            return None
        elif valType == int:
            if string.isnumeric():
                return int(string)
            return None
        elif valType == bool:
            lower = string.lower()
            if lower in ("t", "true"):
                return True
            elif lower in ("f", "false"):
                return False
            return None
        elif valType == str:
            return string
        elif valType == list:
            if len(string) < 2:
                return None
            if string[0] != "[":
                return None
            if string[-1] != "]":
                return None
            val = [self.stringToVal(v, None) for v in string[1:-1].split(",")]
            if None in val:
                return None
            return val
        elif valType == None:
            try:
                return eval(string)
            except:
                return None
        else:
            try:
                valType(string)
            except:
                return None
        
    def updateVar(self, *args):
        if self.edit:
            text = self.textVar.get()
            val = self.stringToVal(text, type(self.getVal()))
            if val is None:
                return
            #Access variables through parent-child tree, plus indexes
            obj = self.obj
            lastVarName = None
            lastIndex = None
            for varName in self.varName:
                if lastIndex is not None:
                    obj = obj[lastIndex]
                if lastVarName is not None:
                    obj = getattr(obj, lastVarName)
                varName = varName.replace("]", "").split("[")
                if len(varName) > 1:
                    obj = getattr(obj, varName[0])
                    for index in varName[1:-1]:
                        obj = obj[int(index)]
                    lastIndex = int(varName[-1])
                else:
                    lastVarName = varName[0]
                    lastIndex = None
            if lastIndex is None:
                setattr(obj, self.varName[-1], val)
            else:
                #print(obj, lastIndex, val)
                obj[lastIndex] = val
            print("Set " + ".".join(self.varName) + " to " + text)
            #print("New Value", self.getVal())
            self.updated = True
    
    def updateSelf(self):
        val = self.getVal()
        if val != self.prevVal:
            self.textVar.set(self.valToString(val))
        self.prevVal = val
        self.updated = False
    
    def updateAll():
        for display in VarDisplay.displays:
            display.updateSelf()
            
    def updateVarDisplayList(l):
        for display in l:
            display.updateSelf()
            
    def delete(self):
        VarDisplay.displays.remove(self)
        self.destroy()