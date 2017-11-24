import os
from os.path import basename
from encoder import Encoder
import encoder
import sys
import os
import h5py
import numpy as np
import json
import shutil

modelFilepath = sys.argv[-1]
modelFolder = os.path.dirname(sys.argv[0])

modelName, ext = os.path.splitext(basename(modelFilepath))

outputFolderPath = modelFolder + '\\' + modelName + '_KerasJSInput\\'

shutil.rmtree(outputFolderPath, ignore_errors=True)

os.makedirs(outputFolderPath)

outputArchitectureConfigFilepath = outputFolderPath + 'architectureConfig.json'
preOutputWeightsFilepath = outputFolderPath + 'preOutputWeights.buf'

from keras.models import load_model
model = load_model(modelFilepath)

model.save_weights(preOutputWeightsFilepath)

with open(outputArchitectureConfigFilepath, 'w') as f:
    f.write(model.to_json())

encoder = Encoder(preOutputWeightsFilepath)
encoder.serialize()
encoder.save()