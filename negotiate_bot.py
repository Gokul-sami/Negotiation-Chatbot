from flask import Flask, request, jsonify
import openai
from textblob import TextBlob
import requests

app = Flask(__name__)

# Replace with your OpenAI API Key
openai.api_key = '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'

# Initial pricing logic
INITIAL_PRICE = 100
MIN_PRICE = 50

# Function to analyze sentiment of the user's message
def analyze_sentiment(user_message):
    blob = TextBlob(user_message)
    sentiment = blob.sentiment.polarity
    return sentiment

# Function to handle negotiation using GPT
def generate_gpt_response(user_offer, current_price):
    prompt = f"""
    You are a supplier negotiating a price with a customer. The initial price for the product is ${INITIAL_PRICE}. 
    The customer has offered ${user_offer}. Negotiate the price, respond with a counteroffer or accept/reject the offer.
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # or use "gpt-4" if you have access
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100
    )
    
    return response['choices'][0]['message']['content'].strip()

# Function to call an external negotiation API
def call_external_negotiation_api(user_offer, current_price):
    api_url = "http://localhost:5001/negotiate"  # Updated to mock API
    
    payload = {
        "user_offer": user_offer,
        "current_price": current_price
    }
    
    # Make the API call
    response = requests.post(api_url, json=payload)
    
    # Handle the response from the external API
    if response.status_code == 200:
        return response.json()  # Expecting a JSON response
    else:
        return {"message": "Error in negotiating with external service."}

# Function to handle the negotiation logic with sentiment analysis
def handle_negotiation(user_offer, user_message):
    # Analyze the sentiment of the user's message
    sentiment = analyze_sentiment(user_message)
    
    # Adjust discount based on sentiment
    if sentiment > 0.5:  # Positive sentiment
        discount = 15  # Better discount for polite/positive users
    elif 0 < sentiment <= 0.5:  # Neutral sentiment
        discount = 10  # Moderate discount
    else:  # Negative sentiment
        discount = 5  # Lower discount for negative tone

    # Adjust final price based on discount
    final_price = INITIAL_PRICE - discount

    # Negotiation logic
    if user_offer >= final_price:
        return {"message": f"Deal accepted at ${final_price}!"}
    elif user_offer < MIN_PRICE:
        return {"message": "Offer too low, unable to accept.", "counteroffer": MIN_PRICE}
    else:
        # Call external negotiation API for further negotiation
        return call_external_negotiation_api(user_offer, final_price)

# API endpoint to start negotiation
@app.route('/negotiate', methods=['POST'])
def negotiate():
    # Get user's price offer and message from the request
    user_offer = request.json.get('user_offer')
    user_message = request.json.get('user_message')

    # Ensure user offer is valid
    if not user_offer or not isinstance(user_offer, (int, float)):
        return jsonify({"error": "Invalid input. Please provide a numeric value for user offer."}), 400

    if not user_message or not isinstance(user_message, str):
        return jsonify({"error": "Invalid input. Please provide a message to analyze."}), 400

    # Handle the negotiation
    response = handle_negotiation(user_offer, user_message)
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
