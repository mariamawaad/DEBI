from flask import Flask, request, jsonify
from pymongo import MongoClient
from collections import Counter


app = Flask(__name__)

client = MongoClient("mongodb+srv://Mariam:123@clusterm.rtobw.mongodb.net/?retryWrites=true&w=majority&appName=ClusterM")
db = client["StudentsDB"]
collection = db["messages"]

@app.route('/')
def root():
    return jsonify({'message': 'Welcome to the Flask REST API!'})

@app.route('/add_message', methods=['GET'])
def add_message():
    # Get the message, subject, and class_name from query parameters
    message = request.args.get('message')
    subject = request.args.get('subject')
    class_name = request.args.get('class_name')

    # Sentiment analysis: check if the message contains the word "good"
    if message and "good" in message.lower():
        sentiment = "positive"
    else:
        sentiment = "negative"

    # Store the message along with sentiment in the database
    collection.insert_one({
        'message': message,
        'subject': subject,
        'class_name': class_name,
        'sentiment': sentiment
    })
@app.route('/update_sentiment', methods=['GET'])
def update_sentiment():
    # Retrieve all documents
    messages = collection.find()

    # Iterate through all documents and update sentiment based on the message
    for message in messages:
        # Analyze sentiment (basic logic: check if "good" exists in the message)
        message_text = message.get('message', '')
        if "good" in message_text.lower():
            sentiment = "positive"
        else:
            sentiment = "negative"

        # Update the sentiment in MongoDB
        collection.update_one(
            {'_id': message['_id']},
            {'$set': {'sentiment': sentiment}}
        )

    return jsonify({'message': 'Sentiments updated for all messages successfully!'})


    return jsonify({'message': 'Message added successfully!', 'sentiment': sentiment})
@app.route('/messages')
def get_messages():
    # Fetch messages from MongoDB and convert ObjectId to string
    messages = list(collection.find())
    
    # Convert _id to string for JSON serialization
    for message in messages:
        message['_id'] = str(message['_id'])
    
    return jsonify(messages)

@app.route('/analyze')
def analyze():
    group_by = request.args.get('group_by')
    
    # Fetch all messages
    messages = list(collection.find())
    
    # If no group_by is provided, compute the overall mode sentiment
    if group_by is None:
        sentiments = [message['sentiment'] for message in messages]
        sentiment_counter = Counter(sentiments)
        mode_sentiment, _ = sentiment_counter.most_common(1)[0]
        return jsonify({'mode_sentiment': mode_sentiment})

    # If group_by is provided, group sentiment analysis by the specified parameter (class_name or subject)
    grouped_data = {}
    for message in messages:
        group_key = message.get(group_by)
        if group_key:
            if group_key not in grouped_data:
                grouped_data[group_key] = []
            grouped_data[group_key].append(message['sentiment'])

    # Calculate mode sentiment for each group
    result = {}
    for group_key, sentiments in grouped_data.items():
        sentiment_counter = Counter(sentiments)
        mode_sentiment, _ = sentiment_counter.most_common(1)[0]
        result[group_key] = mode_sentiment

    return jsonify(result)
@app.route('/search', methods=['GET'])
def get_messages_by_sentiment():
    # Get the sentiment query parameter from the request
    sentiment = request.args.get('query')

    # Check if sentiment is provided
    if not sentiment:
        return jsonify({'error': 'Sentiment query parameter is required'}), 400

    # Retrieve messages that match the given sentiment
    messages = list(collection.find({'sentiment': sentiment}))

    # Convert _id to string for JSON serialization
    for message in messages:
        message['_id'] = str(message['_id'])

    # Return the filtered messages as JSON
    return jsonify(messages)

if __name__ == '__main__':
    app.run(debug=True)