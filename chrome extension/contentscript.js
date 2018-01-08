function getId(entry) {
    return entry.getAttribute("id");
}

function getTitle(entry) {
    return entry.getAttribute("data-title");
}

function getThumbnailUrl(entry) {
    var style = null;

    var visuals = entry.getElementsByClassName('visual');

    for (var i = 0; i < visuals.length; i++) {
        var visual = visuals[i];

        if (visual.className == 'visual') {
            var style = visual.getAttribute('style');
        }
    }

    if (style == null) {
        return null;
    }

    var result = style.substring(style.indexOf('url(\"') + 5);
    result = result.replace('\");', '');

    return result;
}

function getSummary(entry) {
    return entry.getElementsByClassName('summary')[0].textContent;
}

function getSource(entry) {
    return entry.getElementsByClassName('source')[0].textContent;
}

function notifyBackgroundScript(entry, opened) {
    var message = {
        messageId: 'storeUserAction',
        id: getId(entry),
        title: getTitle(entry),
        thumbnailUrl: getThumbnailUrl(entry),
        summary: getSummary(entry),
        source: getSource(entry),
        opened: opened
    };

    console.log('Sending storeUserAction request [opened: ' + message.opened + ', source: ' + message.source + ', title: ' + message.title + ', summary: ' + message.summary + ', id: ' + message.id + ', thumbnailUrl: ' + message.thumbnailUrl + ']')

    chrome.runtime.sendMessage(message);
}

function sendPredictionRequest(entry) {
    var message = {
        messageId: 'predictImportance',
        title: getTitle(entry),
        thumbnailUrl: getThumbnailUrl(entry),
        summary: getSummary(entry),
        source: getSource(entry)
    };

    console.log('Sending predictImportance request [source: ' + message.source + ', title: ' + message.title + ', summary: ' + message.summary + ', thumbnailUrl: ' + message.thumbnailUrl + ']')

    chrome.runtime.sendMessage(message, onPredictionMessageResponse.bind(this, entry));
}

function onPredictionMessageResponse(entry, response) {
    var title = getTitle(entry)
    var thumbnailUrl = getThumbnailUrl(entry)
    var summary = getSummary(entry)
    var source = getSource(entry)
    var predictedImportance = response.predictedImportance[0]

    console.log('Received predictImportance responce [predictedImportance: ' + predictedImportance + ', source: ' + source + ', title: ' + title + ', summary: ' + summary + ', thumbnailUrl: ' + thumbnailUrl + ']')

    var percent = entry.querySelectorAll('.percent');

    if (percent.length == 0) {
        markPrediction(entry, predictedImportance);
    }
}

function onMouseDown(e) {
    switch (e.target.className) {
        case 'visual-overlay':
        case 'summary':
        case 'hide dark':
            if (e.button == 1) {
                e.preventDefault();
            }
            break;
    }
}

function onMouseUp(e) {
    switch (e.target.className) {
        case 'visual-overlay':
        case 'summary':
            if (e.which == 1) {
                notifyBackgroundScript(e.target.parentNode.parentNode, true);
            }

            if (e.which == 2) {
                return false;
            }
            break;

        case 'title':
            if (e.which == 1 || e.which == 2) {
                notifyBackgroundScript(e.target.parentNode.parentNode, true);
            }
            break;

        case 'hide dark':
            if (e.which == 1) {
                notifyBackgroundScript(e.target.parentNode.parentNode.parentNode, false);
            }
            break;
    }
}

function registerEntryListeners() {
    var entries = document.querySelectorAll('.entry');

    for (var i = 0; i < entries.length; i++) {
        var entry = entries[i];

        if (entry.onmouseup == null) {
            entry.onmouseup = onMouseUp;
            entry.onmousedown = onMouseDown;
        }
    }
}

function hsl_col_perc(value, start, end) {
    var c = end * value + start;

    //Return a CSS HSL string
    return 'hsl(' + c + ',100%,50%)';
}

var jsInitChecktimer = setInterval(checkForJS_Finish, 1000);

function predictAndMarkImportance() {
    var entries = document.querySelectorAll('.entry');

    for (var i = 0; i < entries.length; i++) {
        var entry = entries[i];

        var percent = entry.querySelectorAll('.percent');

        if (percent.length == 0) {
            var waiting = entry.classList.contains('waiting')
            
            if(waiting == false) {
                entry.classList.add('waiting')

                var prediction = predict(entry);
            }
        }
    }
}

function markPrediction(entry, prediction) {
    var span = document.createElement('span');

    span.position = 'relative';
    span.className = 'percent';

    span.appendChild(document.createTextNode(prediction.toFixed(2)));
    span.style.background = hsl_col_perc(prediction, 0, 120);
    span.style.height = 'fit-content';
    span.style.width = 'fit-content';
    span.style.color = '#000000';
    span.style.paddingLeft = '2px';
    span.style.paddingTop = '1px';
    span.style.paddingRight = '2px';

    var visual = getVisualElement(entry);

    visual.appendChild(span);

    entry.classList.remove('waiting')
}

function getVisualElement(entry) {
    var visuals = entry.getElementsByClassName('visual');

    for (var i = 0; i < visuals.length; i++) {
        var visual = visuals[i];

        if (visual.className == 'visual' || visual.className == 'visual placeholder') {
            return visual;
        }
    }

    return null;
}

function predict(entry) {
    sendPredictionRequest(entry);
}

function checkForJS_Finish() {
    predictAndMarkImportance();
    registerEntryListeners();
}