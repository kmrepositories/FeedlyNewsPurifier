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

	dbx.filesListFolder({
		path: ''
	})
		.then(function (response) {
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
		.catch(function (error) {
			console.error(error);

			return false
		});
}

function onPredictImportanceMessage(message, sendResponse) {
	predict(message).then(onPredictionReady.bind(this, sendResponse))
}

function onPredictionReady(sendResponse, prediction) {
	sendResponse({
		predictedImportance: prediction
	});
}

function createDropbox() {
	return new Promise(function (resolve, reject) {
		var xobj = new XMLHttpRequest();

		xobj.open('GET', 'dropboxApiToken.json');

		xobj.onreadystatechange = function () {
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
		dbx.filesDownload({ path: '/model/modelInputMetadata.json' }).then(file => {
			var reader = new FileReader();

			reader.onload = function (e) {
				resolve(JSON.parse(reader.result))
			}

			reader.readAsText(file.fileBlob)
		})
	});
}

function covertToSequenceOfWords(sequenceOfCharacters) {
	sequenceOfCharacters = sequenceOfCharacters.trim()
	var filteredSequenceOfCharacters = ''
	var filterString = '!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\t\n'

	for(i = 0; i < sequenceOfCharacters.length; i++) {
		var character = sequenceOfCharacters[i]

		if(filterString.indexOf(character) > -1) {
			filteredSequenceOfCharacters = filteredSequenceOfCharacters.concat(' ')
		} else {
			filteredSequenceOfCharacters = filteredSequenceOfCharacters.concat(character)
		}
	}

	filteredSequenceOfCharacters = filteredSequenceOfCharacters.replace(/  +/g, ' ');

	var words = filteredSequenceOfCharacters.split(' ')
	
	var lowercaseWords = []
	
	for(i = 0; i < words.length; i++) {
		lowercaseWords.push(words[i].toLowerCase())
	}

	return lowercaseWords
}

function convertToSequenceOfTokens(sequenceOfWords, word_index) {
	var sequenceOfTokens = []

	for(i = 0; i < sequenceOfWords.length; i++) {
		var word = sequenceOfWords[i]

		sequenceOfTokens.push(0)
		
		var th = Object.keys(word_index).length

		for(l = 0; l < th; l++) {
			v1 = word_index[l]

			if(v1 == word) {
				sequenceOfTokens[sequenceOfTokens.length - 1] = l

				break
			}
		}
	}
	
	console.log(sequenceOfWords)
	console.log(sequenceOfTokens)

	return sequenceOfTokens
}

function prepareModelInput(message) {
	var source = message.source
	var title = message.title
	var summary = message.summary
	var sep = ' qwertyuiop '

	var inputSequence = summary + sep + title + sep + source

	var words = covertToSequenceOfWords(inputSequence)

	var reqSeqLen = modelInputMetadata.requiredSequenceLength
	var word_index = modelInputMetadata.word_index

	var seqOfTok = convertToSequenceOfTokens(words, word_index)

	var diff = reqSeqLen - seqOfTok.length
	
	modelInput = []

	for (i = 0; i < reqSeqLen; i++) {
		if (i < diff) {
			modelInput.push(0)
		} else {
			var tok = seqOfTok[i - diff]

			modelInput.push(tok)
		}
	}

	return modelInput
}

function predict(message) {
	return new Promise(function (mes, resolve, reject) {
		const inputData = {
			'input': new Float32Array(prepareModelInput(mes))
		}

		model.predict(inputData).then((outputData) => {
			resolve(outputData.output)
		})
	}.bind(this, message))
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
	xhr.onload = function () {
		var reader = new FileReader();
		reader.onloadend = function () {
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
		toDataURL(request.thumbnailUrl, function (dataUrl) {
			request.thumbnailUrl = dataUrl;

			dbx.filesUpload({
				path: '/' + createFilename(request),
				contents: JSON.stringify(request)
			})
				.then(function (response) {
					console.log(response);
				})
				.catch(function (error) {
					console.log(error);
				})
		})
	} else {
		dbx.filesUpload({
			path: '/' + createFilename(request),
			contents: JSON.stringify(request)
		})
			.then(function (response) {
				console.log(response);
			})
			.catch(function (error) {
				console.log(error);
			})
	}
}

function getModelFilesUrls() {
	return new Promise(function (resolve, reject) {
		var promises = []

		promises.push(dbx.filesDownload({ path: '/model/modelArchitecture.json' }))
		promises.push(dbx.filesDownload({ path: '/model/modelWeights.buf' }))
		promises.push(dbx.filesDownload({ path: '/model/modelWeightsMetadata.json' }))

		Promise.all(promises).then(values => {
			var modelArchitectureUrl = URL.createObjectURL(values[0].fileBlob)
			var modelWeightsUrl = URL.createObjectURL(values[1].fileBlob)
			var modelWeightsMetadataUrl = URL.createObjectURL(values[2].fileBlob)

			resolve([modelArchitectureUrl, modelWeightsUrl, modelWeightsMetadataUrl])
		})
	})
}

function createModel() {
	return new Promise(function (resolve, reject) {
		getModelFilesUrls().then(result => {
			var modelArchitectureUrl = result[0]
			var modelWeightsUrl = result[1]
			var modelWeightsMetadata = result[2]

			var KerasJS = require('keras-js');

			let model = new KerasJS.Model({
				filepaths: {
					model: modelArchitectureUrl,
					weights: modelWeightsUrl,
					metadata: modelWeightsMetadata
				},
				gpu: true
			})

			model.ready().then(() => {
				resolve(model)
			})
		})
	})
}

//-------------------------------------------------------------

var dbx = null
var model = null
var modelInputMetadata = null

createDropbox().then(r1 => {
	dbx = r1

	createModel().then(r2 => {
		model = r2

		loadModelInputMetadata().then((r3) => {
			modelInputMetadata = r3

			chrome.runtime.onMessage.addListener(onRequest)
		})
	})
})