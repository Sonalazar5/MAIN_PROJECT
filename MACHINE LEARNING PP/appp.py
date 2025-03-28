from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np
from pymongo import MongoClient

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Connect to MongoDB Atlas
MONGO_URI = "mongodb+srv://sonalazar:9633591213@cluster0.zs9tqxx.mongodb.net/MainProjectDB?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["MainProjectDB"]
collection = db["products"]

# Load the trained model and encoder
model, encoder = joblib.load("price_model.pkl")


@app.route("/predict", methods=["POST"])
def predict_price():
    try:
        data = request.json
        category = data.get("category")
        product = data.get("product")
        quantity = float(data.get("quantity", 1))  # Default quantity is 1 kg if not provided

        if not all([category, product]):
            return jsonify({"message": "Category and Product are required"}), 400

        # Encode category and product
        encoded_category_product = encoder.transform([[category, product]])

        # Predict price per kg
        price_per_kg = model.predict(encoded_category_product)[0]
        total_price = round(float(price_per_kg) * quantity, 2)

        return jsonify({
            "pricePerKg": round(float(price_per_kg), 2),
            "totalPrice": total_price
        }), 200

    except Exception as e:
        return jsonify({"message": "Error predicting price", "error": str(e)}), 500


@app.route("/addProduct", methods=["POST"])
def add_product():
    try:
        data = request.json
        category = data.get("category")
        product = data.get("product")
        quantity = float(data.get("quantity", 1))  # Default 1 kg if not provided
        farmer_id = data.get("farmerId")

        if not all([category, product, farmer_id, quantity]):
            return jsonify({"message": "Category, Product, Farmer ID, and Quantity are required"}), 400

        # Predict the price per kg
        encoded_category_product = encoder.transform([[category, product]])
        price_per_kg = model.predict(encoded_category_product)[0]
        total_price = round(float(price_per_kg) * quantity, 2)

        # Save to MongoDB
        product_data = {
            "category": category,
            "product": product,
            "pricePerKg": round(float(price_per_kg), 2),
            "quantity": quantity,
            "totalPrice": total_price,
            "farmerId": farmer_id
        }

        result = collection.insert_one(product_data)
        print(f"Inserted ID: {result.inserted_id}")

        return jsonify({
            "message": "Product added successfully",
            "pricePerKg": round(float(price_per_kg), 2),
            "totalPrice": total_price
        }), 201

    except Exception as e:
        print("Error:", e)
        return jsonify({"message": "Error adding product", "error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=8080, debug=True)
