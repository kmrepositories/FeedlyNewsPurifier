# FeedlyNewsPurifier

kfdskfgArtificial neural network based approach to automatically discard not important news in Feedly RSS client.

The premise of this project is to create an automated tool that can help user in a process of discarding not important news from Feedly RSS client. The code accomplishes this with the aid of artificial neural network.

The project consists of two main components:

First component is a Chrome browser extension which is responsible for gathering ANN input data comprising news traits(thumbnail image, source, title, summary) along with the user action(news opened or discarded). That data is then stored in a connected dropbox account for future offline neural network feed process.
Additionally this extension predicts the news importance using available ANN model and marks the importance by adding color indicator on top of news thumbnails.

Second component is a group of Python scripts responsible creation of ANN model and feeding it with data stored in Dropbox.

The project is still in a prototype stage but already manages to predict news importance with promising results.

![alt text](https://github.com/kmrepositories/FeedlyNewsPurifier/blob/master/feedlyAI.jpg)
