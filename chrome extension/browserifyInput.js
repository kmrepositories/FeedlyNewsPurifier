function onRequest(request, sender, sendResponse) {
    var messageId = request.messageId;

    switch (messageId) {
        case 'storeUserAction':
            onStoreUserActionMessage(request);
            break;

        case 'predictImportance':
            onPredictImportanceMessage(request, sendResponse);

            return true

            break;
    }
}

function onStoreUserActionMessage(message) {
    var filename = createFilename(message);
	
	getDropbox().then((dbx) => {
		dbx.filesListFolder({
            path: ''
        })
        .then(function(response) {
            console.log(response);

            var createFile = true;

            for (var i = 0; i < response.entries.length; i++) {
                var entry = response.entries[i];

                if (entry.name == filename) {
                    createFile = false;
                }
            }

            if (createFile == true) {
                createFileInDropbox(message);
            }
        })
        .catch(function(error) {
            console.error(error);

            return false
        });
	})
}

function onPredictImportanceMessage(message, sendResponse) {
    predict(message).then(onThen.bind(this, message, sendResponse))
}

function onThen(message, sendResponse, prediction) {
    sendResponse({
        predictedImportance: prediction
    });
}

function getDropbox() {
	return new Promise(function (resolve, reject) {
		var xobj = new XMLHttpRequest();
	
		xobj.open('GET', 'dropboxApiToken.json');
		
		xobj.onreadystatechange = function() {
			if (xobj.readyState == 4 && xobj.status == "200") {
				    var Dropbox = require('dropbox');
					
					var dbx = new Dropbox({
						accessToken: xobj.responseText
					});
					
					resolve(dbx)
			}
		}
		
		xobj.send(null);
	});
}

function loadModelInputMetadata() {
	return new Promise(function (resolve, reject) {
		var xobj = new XMLHttpRequest();
	
		xobj.open('GET', 'modelInputMetadata.json');
		
		xobj.onreadystatechange = function() {
			if (xobj.readyState == 4 && xobj.status == "200") {
				resolve(JSON.parse(xobj.responseText))
			}
		}
		
		xobj.send(null);
	});
}

function prepareModelInput(message) {
	return new Promise(function (resolve, reject) {
		var source = message.source
		var title = message.title
		var sep = ' ||||| '
		
		loadModelInputMetadata().then((modelInputMetadata) => {		
			var inputSequence = source + sep + title
			
			var diff = modelInputMetadata.requiredSequenceLength - inputSequence.length
			
			modelInput = []
			
			for (i = 0; i < modelInputMetadata.requiredSequenceLength; i++) {
				if (i < diff) {
					modelInput.push(0.0)
				} else {
					var character = inputSequence[i - diff]
					var characterAsInteger = modelInputMetadata.characterToIntegerMap[character]
					var characterAsNormalizedNumber = characterAsInteger / modelInputMetadata.uniqueCharacterCount
					
					modelInput.push(characterAsNormalizedNumber)
				}
			}
			
			resolve(modelInput)
		})
	})
}

function predict(message) {	
	return new Promise(function (resolve, reject) {
		prepareModelInput(message).then((modelInput) => {
			var KerasJS = require('keras-js');
			
			var model = new KerasJS.Model({
				filepaths: {
					model: 'architectureConfig.json',
					weights: 'preOutputWeights_weights.buf',
					metadata: 'preOutputWeights_metadata.json'
				},
				gpu: true
			})
			
			model.ready().then(() => {
				const inputData = {
					'input': new Float32Array(modelInput)
				}

				model.predict(inputData).then((outputData) => {
					resolve(outputData.output)
				})
			})
		})
	})
}

function createIntHash(inputStr) {
    var hash = 0,
        i, chr;
    if (inputStr.length === 0) return hash;
    for (i = 0; i < inputStr.length; i++) {
        chr = inputStr.charCodeAt(i);
        hash = ((hash << 5) - hash) + chr;
        hash |= 0; // Convert to 32bit integer
    }
    return hash;
};

function createFilename(request) {
    var hash = createIntHash(request.title + request.summary + request.source);

    return hash + '.txt';
}

function toDataURL(url, callback) {
    var xhr = new XMLHttpRequest();
    xhr.onload = function() {
        var reader = new FileReader();
        reader.onloadend = function() {
            callback(reader.result);
        }
        reader.readAsDataURL(xhr.response);
    };
    xhr.open('GET', url);
    xhr.responseType = 'blob';
    xhr.send();
}

function createFileInDropbox(request) {
    if (request.thumbnailUrl != null) {
        toDataURL(request.thumbnailUrl, function(dataUrl) {

            request.thumbnailUrl = dataUrl;
			
			getDropbox().then((dbx) => {
				dbx.filesUpload({
                    path: '/' + createFilename(request),
                    contents: JSON.stringify(request)
                })
                .then(function(response) {
                    console.log(response);
                })
                .catch(function(error) {
                    console.log(error);
                })
			})
        })
    } else {
		getDropbox().then((dbx) => {
			dbx.filesUpload({
					path: '/' + createFilename(request),
					contents: JSON.stringify(request)
				})
				.then(function(response) {
					console.log(response);
				})
				.catch(function(error) {
					console.log(error);
				})
		})
    }
}

//-------------------------------------------------------------

chrome.runtime.onMessage.addListener(onRequest);