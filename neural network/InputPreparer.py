from DataGatherer import DataGatherer
import numpy
import os
import json
import random
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import RandomOverSampler
import Common
import keras
from keras.preprocessing import text
from keras.preprocessing import sequence

##############################################################################

class InputPreparer:
    def prepareInput(self):
        sourceFeatures, titleFeatures, summaryFeatures, targets = self._loadFeaturesAndTargets2()

        featuresAsSequencesOfWordTokens, word_index = self._convertFeaturesToSequencesOfWordTokens(sourceFeatures, titleFeatures, summaryFeatures)

        sequenceLenght = self._getLengthOfLongestSequence(featuresAsSequencesOfWordTokens)

        paddedSequences = sequence.pad_sequences(featuresAsSequencesOfWordTokens, maxlen=sequenceLenght)

        self._storeModelInputMetadata(word_index, sequenceLenght)

        paddedSequences, targets = self._shuffleInput(paddedSequences, targets)

        trainSamples, trainTargets, testSamples, testTargets = self._splitIntoTrainAndTest(paddedSequences, targets)

        balancedSamples, balancedTargets, remainingSamples, remainingTargets = self._balanceInput(trainSamples, trainTargets)

        balancedSamples, balancedTargets = self._shuffleInput(balancedSamples, balancedTargets)

        trainPartSamples, validationSamples, trainPartTargets, validationTargets = train_test_split(balancedSamples, balancedTargets, test_size = 0.33)

        trainSamples = remainingSamples
        trainSamples.extend(trainPartSamples)

        trainTargets = remainingTargets
        trainTargets.extend(trainPartTargets)

        trainSamples, trainTargets = self._oversampleInput(trainSamples, trainTargets)

        trainSamples, trainTargets = self._shuffleInput(trainSamples, trainTargets)

        trainSamples.extend(validationSamples)
        trainTargets.extend(validationTargets)

        trainSamples, trainTargets, testSamples, testTargets = self._convertToNumpyArrays(trainSamples, trainTargets, testSamples, testTargets)

        return trainSamples, trainTargets, testSamples, testTargets, len(word_index) + 1

    _SEPARATOR = ' qwertyuiop '
    _TRAIN_TEST_RATIO = 1

    def _splitSetsBasedOnTarget(self, trainSamples, trainTargets):
        positiveSamples = []
        positiveTargets = []
        negativeSamples = []
        negativeTargets = []

        for i in range(len(trainTargets)):
            sample = trainSamples[i]
            target = trainTargets[i]

            if target < 0.5:
                negativeSamples.append(sample)
                negativeTargets.append(target)
            else:
                positiveSamples.append(sample)
                positiveTargets.append(target)

        return positiveSamples, positiveTargets, negativeSamples, negativeTargets

    def _balanceInput(self, trainSamples, trainTargets):
        positiveSamples, positiveTargets, negativeSamples, negativeTargets = self._splitSetsBasedOnTarget(trainSamples, trainTargets)

        negativeCount = len(negativeSamples)
        positiveCount = len(positiveSamples)

        maxCount = min(negativeCount, positiveCount)

        balancedSamples = []
        balancedTargets = []

        balancedSamples.extend(negativeSamples[:maxCount])
        balancedSamples.extend(positiveSamples[:maxCount])

        balancedTargets.extend(negativeTargets[:maxCount])
        balancedTargets.extend(positiveTargets[:maxCount])

        remainingSamples = []
        remainingTargets = []

        if(negativeCount < positiveCount):
            remainingSamples.extend(positiveSamples[maxCount:])
            remainingTargets.extend(positiveTargets[maxCount:])
        elif(negativeCount > positiveCount):
            remainingSamples.extend(negativeSamples[maxCount:])
            remainingTargets.extend(negativeTargets[maxCount:])

        return balancedSamples, balancedTargets, remainingSamples, remainingTargets

    def _convertToNumpyArrays(self, trainSamples, trainTargets, testSamples, testTargets):
        trainSamples = numpy.array(trainSamples)
        trainSamples = trainSamples.reshape((trainSamples.shape[0], trainSamples.shape[1], 1))

        trainTargets = numpy.array(trainTargets)

        if testSamples is not None:
            testSamples = numpy.array(testSamples)
            testSamples = testSamples.reshape((testSamples.shape[0], testSamples.shape[1], 1))

            testTargets = numpy.array(testTargets)

        return trainSamples, trainTargets, testSamples, testTargets

    def _splitIntoTrainAndTest(self, samples, targets):
        trainSamples, testSamples, trainTargets, testTargets = train_test_split(samples, targets, test_size=1 - self._TRAIN_TEST_RATIO, shuffle = False)

        testSamples = None if len(testSamples) == 0 else testSamples
        testTargets = None if len(testTargets) == 0 else testTargets

        return trainSamples, trainTargets, testSamples, testTargets

    def _storeModelInputMetadata(self, word_index, requiredSequenceLength):
        word_index = {v:k for k,v in word_index.items()}

        jsonInput = {'requiredSequenceLength' : requiredSequenceLength, 'word_index' : word_index}

        with open(Common.MODEL_INPUT_METADATA_FILE, 'w', encoding='utf-8') as f:
            f.write(json.dumps(jsonInput))

    def _getLengthOfLongestSequence(self, sequences):
        maxLength = 0

        for sequence in sequences:
            sequenceLength = len(sequence)

            if sequenceLength > maxLength:
                maxLength = sequenceLength

        return maxLength

    def _convertFeaturesToSequencesOfWordTokens(self, sourceFeatures, titleFeatures, summaryFeatures):
        tokenizer = text.Tokenizer()

        listOfFeaturesAsSingleString = []

        for i in range(len(sourceFeatures)):
            sourceFeature = sourceFeatures[i]
            titleFeature = titleFeatures[i]
            summaryFeature = summaryFeatures[i]

            featuresAsSingleString = summaryFeature + self._SEPARATOR + titleFeature + self._SEPARATOR + sourceFeature

            listOfFeaturesAsSingleString.append(featuresAsSingleString)

        tokenizer.fit_on_texts(listOfFeaturesAsSingleString)

        return tokenizer.texts_to_sequences(listOfFeaturesAsSingleString), tokenizer.word_index

    def _loadFeaturesAndTargets2(self):
        data = DataGatherer().gatherData()

        sourceFeatures = data[:, [1]].flatten()
        titleFeatures = data[:, [2]].flatten()
        summaryFeatures = data[:, [3]].flatten()
        targets = data[:, [4]].flatten()
        targets = [(1 if target == 'True' else 0) for target in targets]

        return sourceFeatures, titleFeatures, summaryFeatures, targets

    def _oversampleInput(self, samples, targets):
        oversampler = RandomOverSampler()

        oversampledSamples, oversampledTargets = oversampler.fit_sample(samples, targets)

        return oversampledSamples.tolist(), oversampledTargets.tolist()

    def _shuffleInput(self, samples, targets):
        zipped = list(zip(samples, targets))

        random.shuffle(zipped)

        samples, targets = zip(*zipped)

        samples = [list(a) for a in samples]
        targets = list(targets)

        return samples, targets

    def _extractFeaturesAndTargets(self, dataEntry):
        target = 0 if dataEntry[4] == 'False' else 1
        sourceFeature = dataEntry[1]
        titleFeature = dataEntry[2]
        summaryFeature = dataEntry[3]

        return sourceFeature, titleFeature, summaryFeature, target