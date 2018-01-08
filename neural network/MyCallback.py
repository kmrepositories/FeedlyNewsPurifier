import keras
import datetime
import time
import os
from ModelPackageCreator import ModelPackageCreator

class MyCallback(keras.callbacks.Callback):
    def __init__(self):
        self._bestValidationAccuracy = 0.0
        self._bestValidationLoss = 100.0

    def on_train_begin(self, logs={}):
        self._createRunFolder()

        self._modelPackageCreator = ModelPackageCreator(self._folderName)

    def on_epoch_end(self, epoch, logs={}):
        validationAccuracy = logs.get('val_acc')
        validationLoss = logs.get('val_loss')

        if validationAccuracy > self._bestValidationAccuracy  and validationLoss < self._bestValidationLoss:
            print('\nCreating model package for new best model[val_loss: {}, val_acc: {}]'.format(validationLoss, validationAccuracy))

            self._bestValidationAccuracy = validationAccuracy
            self._bestValidationLoss = validationLoss

            self._modelPackageCreator.createModelPackage(self.model)

            self.model.save_weights(os.path.join(self._folderName, 'modelWeights_{}_{:.3f}_{:.3f}.hdf5'.format(epoch, validationLoss, validationAccuracy)))

    _folderName = ''

    def _createRunFolder(self):
        self._folderName = datetime.datetime.now().strftime('RUN %Y%m%d%H%M%S')

        os.mkdir(self._folderName)