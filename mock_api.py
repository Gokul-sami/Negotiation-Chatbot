from flask import Flask, request, jsonify

mock_app = Flask(__name__)

@mock_app.route('/negotiate', methods=['POST'])
def mock_negotiate():
    user_offer = request.json.get('user_offer')
    current_price = request.json.get('current_price')
    response_message = f"Counteroffer based on your offer of ${user_offer} and current price of ${current_price}."
    return jsonify({"message": response_message, "counteroffer": current_price - 10})  # Example logic

if __name__ == '__main__':
    mock_app.run(debug=True, port=5001)  # This will run on http://localhost:5001
