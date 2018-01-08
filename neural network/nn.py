from MyCallback import MyCallback
import Common
import numpy
import random
from keras.models import Sequential
from keras.layers import Dense, Activation, LSTM, Dropout, Embedding, Flatten
from keras.callbacks import ModelCheckpoint
from keras.optimizers import Adam, SGD
import keras
import os
import tensorflow
from keras.callbacks import TensorBoard
from InputPreparer import InputPreparer
import subprocess

######################################################

def createModel(features, wordCount):
    model = Sequential()
    model.add(Embedding(wordCount, 32, input_length=features.shape[1]))
    model.add(Flatten())
    model.add(Dense(NEURON_COUNT, activation='relu'))
    model.add(Dropout(DROPOUT))
    model.add(Dense(1, activation='sigmoid'))
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    print(model.summary())

    return model

def createCallbackList():
    myCallback = MyCallback()
    remote = keras.callbacks.RemoteMonitor(root='http://localhost:9000')
    tensorboard = TensorBoard(log_dir='./logs', histogram_freq=1, write_graph=True, write_grads = True, write_images=True)

    return [remote, myCallback]

def evaluateModel(model, testSamples, testTargets):
    filteredTestSamples = []
    filteredTestTargets = []

    for i in range(len(testSamples)):
        testSample = testSamples[i]
        testTarget = testTargets[i]

        if testTarget > 0.5:
            filteredTestSamples.append(testSample)
            filteredTestTargets.append(testTarget)

    filteredTestSamples = numpy.array(filteredTestSamples)

    predictions = model.predict(filteredTestSamples)

    print(predictions[:30])

    interestingsNewsCount = len(filteredTestSamples)
    discardPredictionCount = sum(1 for p in predictions if p < 0.5)

    score = (1 - (discardPredictionCount / interestingsNewsCount)) * 100

    print("My Accuracy: %.5f%%" % (score))

    return score

def fitModel(model, trainSamples, trainTargets, callbacks):
    model.fit(trainSamples, trainTargets, batch_size = BATCH_SIZE, epochs = EPOCH_COUNT, callbacks = callbacks, validation_split = TRAIN_VALIDATION_RATIO)

def initializeRandomGenerators():
    RANDOM_SEED = 7

    numpy.random.seed(RANDOM_SEED)
    random.seed(RANDOM_SEED)
    os.environ['PYTHONHASHSEED'] = str(RANDOM_SEED)
    tensorflow.set_random_seed(RANDOM_SEED)

def runVisualizer():
    subprocess.Popen(['python', 'hualos/api.py'], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

######################################################

initializeRandomGenerators()

######################################################

BATCH_SIZE = 1500
EPOCH_COUNT = 150000
TRAIN_VALIDATION_RATIO = 0.33
TRAIN_TEST_RATIO = 1
LEARN_RATE = 0.001
NEURON_COUNT = 10
DROPOUT = 0.0
OPTIMIZER = SGD(LEARN_RATE, momentum=0.95, nesterov=True)
#OPTIMIZER = Adam(LEARN_RATE)

#################################################################

if __name__ == '__main__':

    initializeRandomGenerators()

    runVisualizer()

    trainSamples, trainTargets, testSamples, testTargets, wordCount = InputPreparer().prepareInput()

    #BATCH_SIZE = (int)(len(trainSamples) / 2)

    trainSamples = trainSamples.reshape((trainSamples.shape[0], trainSamples.shape[1]))

    model = createModel(trainSamples, wordCount)

    callbacks = createCallbackList()

    fitModel(model, trainSamples, trainTargets, callbacks)

    if testSamples is not None:
        evaluateModel(model, testSamples, testTargets)
