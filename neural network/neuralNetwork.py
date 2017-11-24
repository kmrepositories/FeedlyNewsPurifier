import numpy
from keras.models import Sequential
from keras.layers import Dense, Activation, LSTM, Dropout
from keras.callbacks import ModelCheckpoint
from keras.optimizers import Adam
import random
from imblearn.over_sampling import RandomOverSampler
import json

######################################################

INPUT_FILE = 'input/!textInput.txt'
MODEL_INPUT_METADATA_FILE = 'modelInputMetadata.json'
BATCH_SIZE = 512
EPOCH_COUNT = 1000
TRAIN_VALIDATION_RATIO = 0.33
RANDOM_SEED = 7
TRAIN_TEST_RATIO = 0.7
SEPARATOR = ' ||||| '

######################################################

def storeModelInputMetadata(uniqueCharacterCount, characterToIntegerMap, requiredSequenceLength):
    jsonInput = {'uniqueCharacterCount' : uniqueCharacterCount, 'characterToIntegerMap' : characterToIntegerMap, 'requiredSequenceLength' : requiredSequenceLength}

    with open(MODEL_INPUT_METADATA_FILE, 'w', encoding='utf-8') as modelInputMetadataFile:
        modelInputMetadataFile.write(json.dumps(jsonInput))

def extractFeaturesAndTargets(line):
    elements = line.split(SEPARATOR)

    target = 0 if elements[1] == 'False' else 1
    sourceFeature = elements[2]
    titleFeature = elements[3]

    return sourceFeature, titleFeature, target

def loadFeaturesAndTargets():
    sourceFeatures = []
    titleFeatures = []
    targets = []

    with open(INPUT_FILE, 'r', encoding='utf-8') as inputFile:
        for line in inputFile:
            sourceFeature, titleFeature, target = extractFeaturesAndTargets(line)

            sourceFeatures.append(sourceFeature)
            titleFeatures.append(titleFeature)
            targets.append(target)

    return sourceFeatures, titleFeatures, targets

def getUniqueCharacters(sequencesOfCharacters):
    allTextsAsOne = []

    for sequenceOfCharacters in sequencesOfCharacters:
        allTextsAsOne = allTextsAsOne + sequenceOfCharacters

    return sorted(list(set(allTextsAsOne)))

def convertFeaturesToSequencesOfCharacters(sourceFeatures, titleFeatures):
    result = []

    for i in range(len(sourceFeatures)):
        sequenceOfCharacters = []

        sourceFeature = sourceFeatures[i]
        titleFeature = titleFeatures[i]

        sequenceOfCharacters.extend(sourceFeature)
        sequenceOfCharacters.extend(SEPARATOR)
        sequenceOfCharacters.extend(titleFeature)

        result.append(sequenceOfCharacters)

    return result

def convertToSequencesOfNormalizedNumbers(sequencesOfCharacters, uniqueCharacters, characterToIntegerMap):
    uniqueCharacterCount = len(uniqueCharacters)

    result = []

    for sequenceOfCharacters in sequencesOfCharacters:
        sequenceOfNormalizedNumbers = []

        for character in sequenceOfCharacters:
            characterAsNormalizedNumber = characterToIntegerMap[character] / float(uniqueCharacterCount)

            sequenceOfNormalizedNumbers.append(characterAsNormalizedNumber)

        result.append(sequenceOfNormalizedNumbers)

    return result

def getLengthOfLongestSequence(sequences):
    maxLength = 0

    for sequence in sequences:
        sequenceLength = len(sequence)

        if sequenceLength > maxLength:
            maxLength = sequenceLength

    return maxLength

def padSequences(sequences, sequenceLenght):
    result = []

    for sequence in sequences:
        difference = sequenceLenght - len(sequence)

        paddedSequence = [0.0] * difference
        paddedSequence.extend(sequence)

        result.append(paddedSequence)

    return result

def convertToNumpyArrays(trainSamples, trainTargets, testSamples, testTargets):
    trainSamples = numpy.array(trainSamples)
    trainSamples = trainSamples.reshape((trainSamples.shape[0], trainSamples.shape[1], 1))

    trainTargets = numpy.array(trainTargets)

    testSamples = numpy.array(testSamples)
    testSamples = testSamples.reshape((testSamples.shape[0], testSamples.shape[1], 1))

    testTargets = numpy.array(testTargets)

    return trainSamples, trainTargets, testSamples, testTargets

def prepareInput():
    sourceFeatures, titleFeatures, targets = loadFeaturesAndTargets()

    featuresAsSequencesOfCharacters = convertFeaturesToSequencesOfCharacters(sourceFeatures, titleFeatures)

    uniqueCharacters = getUniqueCharacters(featuresAsSequencesOfCharacters)
    characterToIntegerMap = dict((c, i + 1) for i, c in enumerate(uniqueCharacters))
    sequenceLenght = getLengthOfLongestSequence(featuresAsSequencesOfCharacters)

    storeModelInputMetadata(len(uniqueCharacters), characterToIntegerMap, sequenceLenght)

    featuresAsSequencesOfNormalizedNumbers = convertToSequencesOfNormalizedNumbers(featuresAsSequencesOfCharacters, uniqueCharacters, characterToIntegerMap)

    paddedSequences = padSequences(featuresAsSequencesOfNormalizedNumbers)

    paddedSequences, targets = shuffleInput(paddedSequences, targets)

    trainSamples, trainTargets, testSamples, testTargets = splitIntoTrainAndTest(paddedSequences, targets)

    trainSamples, trainTargets = oversampleInput(trainSamples, trainTargets)

    trainSamples, trainTargets = shuffleInput(trainSamples, trainTargets)

    return convertToNumpyArrays(trainSamples, trainTargets, testSamples, testTargets)

def oversampleInput(samples, targets):
    oversampler = RandomOverSampler()

    oversampledSamples, oversampledTargets = oversampler.fit_sample(samples, targets)

    return oversampledSamples, oversampledTargets

def shuffleInput(samples, targets):
    zipped = list(zip(samples, targets))

    random.shuffle(zipped)

    return zip(*zipped)

def createModel(features):
    model = Sequential()

    model.add(LSTM(25, input_shape=(features.shape[1], features.shape[2])))
    model.add(Dropout(0.2))
    model.add(Dense(1))
    model.add(Activation('sigmoid'))

    model.compile(loss = 'binary_crossentropy', optimizer = Adam(), metrics = ['accuracy'])

    print(model.summary())

    return model

def splitIntoTrainAndTest(samples, targets):
    trainSamples = samples[:int(len(samples) * TRAIN_TEST_RATIO)]
    trainTargets = targets[:int(len(targets) * TRAIN_TEST_RATIO)]

    testSamples = samples[int(len(samples) * TRAIN_TEST_RATIO):]
    testTargets = targets[int(len(targets) * TRAIN_TEST_RATIO):]

    return trainSamples, trainTargets, testSamples, testTargets

def createCallbackList():
    filepath = "weights-improv-{epoch:02d}-{val_acc:.8f}.hdf5"

    checkpoint = ModelCheckpoint(filepath, monitor='val_acc', verbose=1, save_best_only=True, mode='max')

    return [checkpoint]

def evaluateModel(model, testSamples, testTargets):
    for i in range(30):
        testFeature = testSamples[i]
        testFeature = numpy.reshape(testFeature, (1, testFeature.shape[0], testFeature.shape[1]))
        pred = model.predict(testFeature, verbose=0)
        print('{} ## {}'.format(testFeature.flatten(), pred))

    scores = model.evaluate(testSamples, testTargets, verbose=0)

    print("Accuracy: %.5f%%" % (scores[1] * 100))

def fitModel(model, trainSamples, trainTargets):
    model.fit(trainSamples, trainTargets, batch_size = BATCH_SIZE, epochs = EPOCH_COUNT, callbacks = createCallbackList(), validation_split = TRAIN_VALIDATION_RATIO)

def initializeRandomGenerators():
    numpy.random.seed(RANDOM_SEED)
    random.seed(RANDOM_SEED)

#################################################################
initializeRandomGenerators()

trainSamples, trainTargets, testSamples, testTargets = prepareInput()

model = createModel(trainSamples)

fitModel(model, trainSamples, trainTargets)

evaluateModel(model, testSamples, testTargets)
