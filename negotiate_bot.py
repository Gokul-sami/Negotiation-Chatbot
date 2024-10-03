from flask import Flask, request, jsonify
import openai
from textblob import TextBlob
import requests
import os

app = Flask(__name__)

# Load OpenAI API key from environment variables
openai.api_key = os.getenv('OPENAI_API_KEY')

INITIAL_PRICE = 100  # Starting price for negotiation
MIN_PRICE = 50       # Minimum acceptable price

# Store negotiation states for each user
negotiation_state = {}

def analyze_sentiment(user_message):
    """Analyze sentiment of the user's message and return polarity."""
    blob = TextBlob(user_message)
    return blob.sentiment.polarity

def generate_gpt_response(user_offer, current_price):
    """Generate a negotiation response using OpenAI's GPT model."""
    prompt = f"""
    You are a supplier negotiating a price with a customer. The initial price for the product is ${INITIAL_PRICE}. 
    The customer has offered ${user_offer}. Negotiate the price, respond with a counteroffer or accept/reject the offer.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Error in generating response: {str(e)}"

def call_external_negotiation_api(user_offer, current_price):
    """Call an external API for additional negotiation logic."""
    api_url = "http://localhost:5001/negotiate"
    
    payload = {
        "user_offer": user_offer,
        "current_price": current_price
    }
    
    try:
        response = requests.post(api_url, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return {"message": "Error in negotiating with external service."}
    except Exception as e:
        return {"message": f"External API call failed: {str(e)}"}

def handle_negotiation(user_offer, user_message, current_price, user_id):
    """Handle negotiation logic and determine response based on user offer and sentiment."""
    sentiment = analyze_sentiment(user_message)
    
    # Adjust discount based on sentiment
    discount = 15 if sentiment > 0.5 else 10 if sentiment > 0 else 5
    final_price = max(MIN_PRICE, current_price - discount)

    if user_offer >= final_price:
        return {"message": f"Deal accepted at ${user_offer}!"}
    elif user_offer < MIN_PRICE:
        return {"message": "Offer too low, unable to accept.", "counteroffer": MIN_PRICE}
    else:
        counteroffer = max(user_offer + 5, final_price)
        negotiation_state[user_id] = counteroffer
        return {"message": f"Counteroffer: ${counteroffer}.", "counteroffer": counteroffer}

@app.route('/negotiate', methods=['POST'])
def negotiate():
    """API endpoint for initiating negotiation."""
    user_offer = request.json.get('user_offer')
    user_message = request.json.get('user_message')
    user_id = request.json.get('user_id')

    # Validate input
    if not user_offer or not isinstance(user_offer, (int, float)):
        return jsonify({"error": "Invalid input. Please provide a numeric value for user offer."}), 400

    if not user_message or not isinstance(user_message, str):
        return jsonify({"error": "Invalid input. Please provide a message to analyze."}), 400

    current_price = negotiation_state.get(user_id, INITIAL_PRICE)
    response = handle_negotiation(user_offer, user_message, current_price, user_id)

    if "counteroffer" in response:
        negotiation_state[user_id] = response["counteroffer"]

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
