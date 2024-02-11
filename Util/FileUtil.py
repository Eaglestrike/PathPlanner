# -*- coding: utf-8 -*-
"""
Created on Tue Jan  2 18:40:28 2024

@author: degog
"""

from tkinter import filedialog
import json
import os
import pandas as pd

def selectOpenFile(fileTypes, directory = None):
    if directory is None:
        directory = os.cwd()
    filename = filedialog.askopenfile(
                    initialdir = directory,
                    title = "Open file",
                    filetypes = fileTypes)
    return filename

def selectSaveFile(fileTypes, directory = None):
    if directory is None:
        directory = os.cwd()
    filename = filedialog.asksaveasfile(
                    initialdir = directory,
                    title = "Save file",
                    filetypes = fileTypes)
    return filename

def selectSaveTextFile(text, directory = None):
    files = [('Text Document', '*.txt')]
    filename = selectSaveFile(files, directory)
    if filename == "":
        return
    with open(filename, "w") as file:
        file.write(text)
    return filename
        
def selectSaveJsonFile(dictionary, directory = None):
    files = [('Save Json', '*.json')]
    filename = selectSaveFile(files, directory)
    if filename == "":
        return
    with open(filename, "w") as fp:
        json.dump(dictionary, fp)
    return filename

def selectDataframe(directory = None):
    files = [('csv files', '*.csv')]
    filename = selectOpenFile(files, directory)
    if filename == "" or filename is None:
        return
    return pd.read_csv(filename)

def saveJsonFile(dictionary, filepath):
    with open(filepath, "w") as fp:
        json.dump(dictionary, fp)
        
def openJsonFile(filepath):
    if not os.path.isfile(filepath):
        return None
    with open(filepath, "r") as fp:
        dictionary = json.load(fp)
    return dictionary
    