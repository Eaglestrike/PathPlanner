import os
import pandas as pd

import Code.Path as Path


newMaxV = 5.5
newMaxA = 5.5

filesType = ["Far"]

directory = "Saves/"
files = os.listdir(directory)

path = Path.Path(mode = "trapezoidal")
path.maxA = 5.5
path.maxV = 5.5

for f in files:
    if ".csv" not in f:
        continue
    if all([(t not in f) for t in filesType]):
        continue
    path.setDataFrame(pd.read_csv(directory + f))
    path.regenerate()
    path.toDataframe().to_csv(directory + f, index = False, lineterminator='\n')