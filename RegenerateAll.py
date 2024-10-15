import os
import pandas as pd

import Code.Path as Path


newMaxV = 5.5
newMaxA = 10.0

filesType = ["Far"]

#directory = "Saves/"
directory = r"C:/Users/degog/Robotics/2024-RobotCode/src/main/deploy/"
files = os.listdir(directory)

path = Path.Path(mode = "hermite")
path.maxA = newMaxV
path.maxV = newMaxA

for f in files:
    if ".csv" not in f:
        continue
    if all([(t not in f) for t in filesType]):
        continue
    path.setDataFrame(pd.read_csv(directory + f))
    path.regenerate()
    path.toDataframe().to_csv(directory + f, index = False, lineterminator='\n')