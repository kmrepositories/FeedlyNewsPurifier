import json
import Common
import numpy
import os
import dropbox

##############################################################################

class DataGatherer:
    def gatherData(self):
        localInputData = self._loadLocalInputData()

        newInputData = self._collectNewInputData(localInputData)

        combinedInputData = self._combineInputData(localInputData, newInputData)

        self._storeCombinedInputData(combinedInputData)

        return combinedInputData

    def _storeCombinedInputData(self, combinedInputData):
        if not os.path.exists(Common.OUTPUT_FOLDER):
            os.makedirs(Common.OUTPUT_FOLDER)

        numpy.savez_compressed(os.path.join(Common.OUTPUT_FOLDER, Common.DATA_FILE), combinedInputData)

    def _collectNewInputData(self, localInputData):
        newDataFilenames = self._createListOfNewInputFilenames(localInputData)

        dbx = self._getDropbox()

        newInputData = []
        i = 0
        for newDataFilename in newDataFilenames:
            i = i + 1

            print('{}/{}'.format(i, len(newDataFilenames)))

            metadata = None
            result = None

            try:
                metadata, result = dbx.files_download('/' + newDataFilename)
            except Exception as e:
                print(newDataFilename)
                print(e)
                continue

            source, title, summary, thumbnailData, opened = self._extractNewsTraits(result.content)

            newInputData.append([newDataFilename, source, title, summary, opened])

        return newInputData

    def _loadLocalInputData(self):
        result = None

        if os.path.isfile(os.path.join(Common.OUTPUT_FOLDER, Common.DATA_FILE + '.npz')):
            result = numpy.load(os.path.join(Common.OUTPUT_FOLDER, Common.DATA_FILE + '.npz'))['arr_0']

        print("Found {} local input entries".format('no' if result is None else result.shape[0]))

        return result

    def _getDropbox(self):
        dropboxApiToken = os.environ['DROPBOX_API_TOKEN']

        return dropbox.Dropbox(dropboxApiToken)

    def _createListOfNewInputFilenames(self, localData):
        allInputFilenames = self._listAllInputFilenames()

        allLocalFilenames = [] if localData is None else localData[:, [0]].flatten().tolist()

        onlyNewFilenames = list(set(allInputFilenames).symmetric_difference(set(allLocalFilenames)))

        print('Found {} new input files'.format(len(onlyNewFilenames)))

        return onlyNewFilenames

    def _listAllInputFilenames(self):
        dbx = self._getDropbox()

        metadata = dbx.files_list_folder('')
        result = []
    
        for entry in metadata.entries:
            if isinstance(entry, dropbox.files.FolderMetadata):
                continue

            result.append(entry.name)
        
        while(True):
            if metadata.has_more:
                metadata = dbx.files_list_folder_continue(metadata.cursor)

                for entry in metadata.entries:
                    if isinstance(entry, dropbox.files.FolderMetadata):
                        continue

                    result.append(entry.name)
            else:
                break

        return result

    def _extractNewsTraits(self, newsEntryData):
        js = json.loads(newsEntryData.decode("utf-8"))

        title = js['title']
        source = js['source']
        summary = js['summary']
        opened = js['opened']
        thumbnailData = js['thumbnailUrl']

        return source, title, summary, thumbnailData, opened

    def _combineInputData(self, first, second):
        if first is None:
            return numpy.array(second)
        else:
            first = first.tolist()

            first.extend(second)

        return numpy.array(first)