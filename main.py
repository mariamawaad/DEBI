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

    # Return a success response
    return jsonify({
        'message': 'Message added successfully!',
        'stored_data': {
            'message': message,
            'subject': subject,
            'class_name': class_name,
            'sentiment': sentiment
        }
    }), 200

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

@app.route('/analyze', methods=['GET'])
def analyze():
    group_by = request.args.get('group_by')
    messages = list(collection.find())

    if not messages:
        return jsonify({'error': 'No messages found in the database'}), 404

    # Adjust to support 'class' as a valid group_by value
    if group_by not in ['class_name', 'subject', 'class']:
        return jsonify({'error': 'Invalid group_by parameter. Valid values are "class_name", "subject", or "class".'}), 400

    if group_by == 'class':
        group_by = 'class_name'  # treat 'class' as 'class_name'

    grouped_data = {}
    for message in messages:
        group_key = message.get(group_by)
        if group_key:
            if group_key not in grouped_data:
                grouped_data[group_key] = []
            grouped_data[group_key].append(message.get('sentiment', 'neutral'))

    result = {}
    for group_key, sentiments in grouped_data.items():
        sentiment_counter = Counter(sentiments)
        mode_sentiment, _ = sentiment_counter.most_common(1)[0]
        result[group_key] = mode_sentiment

    return jsonify(result)

@app.route('/search', methods=['GET'])
def get_messages_by_sentiment():
    query = request.args.get('query')

    # Check if query is provided
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400

    # Retrieve messages that contain the query word (e.g., "good") in the message
    messages = list(collection.find({'message': {'$regex': query, '$options': 'i'}}))

    # Convert _id to string for JSON serialization
    for message in messages:
        message['_id'] = str(message['_id'])

    return jsonify(messages)


if __name__ == '__main__':
    app.run(debug=True)
