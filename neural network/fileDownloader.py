import base64
import dropbox
import os
import shutil
import json

#################################################################

OUTPUT_FOLDER = 'input/'
OUTPUT_FILE = OUTPUT_FOLDER + '!textInput.txt'
SEPARATOR = ' ||||| '

#################################################################

def listAllFiles(dbx):
    metadata = dbx.files_list_folder('')
    result = []
    
    for entry in metadata.entries:
        if isinstance(entry, dropbox.files.FolderMetadata):
            continue

        result.append(entry)
        
    while(True):
        if metadata.has_more:
            metadata = dbx.files_list_folder_continue(metadata.cursor)

            for entry in metadata.entries:
                if isinstance(entry, dropbox.files.FolderMetadata):
                    continue

                result.append(entry)
        else:
            break

    print('Found {} files'.format(len(result)))

    return result

def eraseOutputFolderContent():
    for root, dirs, files in os.walk(OUTPUT_FOLDER):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))

def prepareOutputFolder():
    if os.path.exists(OUTPUT_FOLDER):
        eraseOutputFolderContent()
    else:
        os.makedirs(OUTPUT_FOLDER)

def extractNewsTraits(newsEntryData):
    js = json.loads(newsEntryData.decode("utf-8"))

    title = js['title']
    source = js['source']
    summary = js['summary']
    opened = js['opened']
    thumbnailData = js['thumbnailUrl']

    return source, title, summary, thumbnailData, opened

def handleThumbnailData(thumbnailData, index):
    if thumbnailData == 'data:':
        thumbnailData = None

    if thumbnailData is not None:
        thumbnailImagetype = thumbnailData.split('/', 1)[1].split(';', 1)[0]
        trimmedThumbnailData = thumbnailData.split('base64,', 1)[1]
        decoded = base64.b64decode(trimmedThumbnailData)

        thumbnailFilepath = '{}{}_{}.{}'.format(OUTPUT_FOLDER, index, metadata.name.replace('.txt', ''), thumbnailImagetype)

        with open(thumbnailFilepath, 'wb') as thumbnailFile:
            thumbnailFile.write(decoded)

def handleNewsTextTraits(source, title, summary, opened):
    output.write('{}{}{}{}{}{}{}{}{}\n'.format(index, separator, opened, separator, source, separator, title, separator, summary))

def processListedFiles(dbx, listedFiles):
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as output:
        index = -1;

        for listedFile in listedFiles:
            index = index + 1

            metadata = None
            result = None

            try:
                metadata, result = dbx.files_download('/' + listedFile.name)
            except Exception as e:
                print(listedFile)
                print(e)
                continue

            source, title, summary, thumbnailData, opened = extractNewsTraits(result.content)

            handleThumbnailData(thumbnailData, index)

            handleNewsTextTraits(source, title, summary, opened)

#################################################################

prepareOutputFolder()

dbx = dropbox.Dropbox(os.environ['DROPBOX_API_TOKEN'])

listedFiles = listAllFiles(dbx)

processListedFiles(dbx, listedFiles)