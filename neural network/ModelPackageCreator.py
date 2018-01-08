import keras
import os
import shutil
import Common
import h5py
import numpy as np
import json

##############################################################################

class ModelPackageCreator:
    def __init__(self, path):
        self._modelPackageFolderPath = path + '/modelPackage/'

        self._prepareEmptyFolder()

    def createModelPackage(self, model):
        self._storeModelArchitecture(model)
        self._storeModelWeights(model)
        self._storeModelInputMetadata()

    def _prepareEmptyFolder(self):
        if os.path.exists(self._modelPackageFolderPath):
            shutil.rmtree(self._modelPackageFolderPath)

        os.mkdir(self._modelPackageFolderPath)

    def _storeModelArchitecture(self, model):
        modelArchitectureFilepath = os.path.join(self._modelPackageFolderPath, 'modelArchitecture.json')

        if not os.path.exists(modelArchitectureFilepath):
            with open(modelArchitectureFilepath, 'w') as f:
                f.write(model.to_json())

    def _storeModelWeights(self, model):
        weights = b''
        metadata = []

        model.save_weights('temp.hdf5')

        hdf5_file = h5py.File('temp.hdf5', mode='r')
        if 'layer_names' not in hdf5_file.attrs and 'model_weights' in hdf5_file:
            f = hdf5_file['model_weights']
        else:
            f = hdf5_file

        layer_names = [n.decode('utf8') for n in f.attrs['layer_names']]
        offset = 0
        for layer_name in layer_names:
            g = f[layer_name]
            weight_names = [n.decode('utf8') for n in g.attrs['weight_names']]
            if len(weight_names):
                for weight_name in weight_names:
                    meta = {}
                    meta['layer_name'] = layer_name
                    meta['weight_name'] = weight_name
                    weight_value = g[weight_name].value
                    bytearr = weight_value.astype(np.float32).tobytes()
                    weights += bytearr
                    meta['offset'] = offset
                    meta['length'] = len(bytearr) // 4
                    meta['shape'] = list(weight_value.shape)
                    meta['type'] = 'float32'
                    metadata.append(meta)
                    offset += len(bytearr)

        hdf5_file.close()

        os.remove('temp.hdf5')

        weights_filepath = os.path.join(self._modelPackageFolderPath, 'modelWeights.buf')
        with open(weights_filepath, mode='wb') as f:
            f.write(weights)

        metadata_filepath = os.path.join(self._modelPackageFolderPath, 'modelWeightsMetadata.json')
        with open(metadata_filepath, mode='w') as f:
            json.dump(metadata, f)

    def _storeModelInputMetadata(self):
        modelInputMetadataFilepath = os.path.join(self._modelPackageFolderPath, Common.MODEL_INPUT_METADATA_FILE)

        if not os.path.exists(modelInputMetadataFilepath):
            os.rename(Common.MODEL_INPUT_METADATA_FILE, os.path.join(self._modelPackageFolderPath, Common.MODEL_INPUT_METADATA_FILE))


##############################################################################