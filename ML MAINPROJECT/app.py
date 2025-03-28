from flask import Flask, request, jsonify
import joblib
from flask_cors import CORS
from pymongo import MongoClient
import pandas as pd



app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Enable CORS for API routes

# Load the Recommendation Model
try:
    recommendation_data = joblib.load("recommendation_model (1).pkl")  # Ensure correct filename
    recommendation_model = recommendation_data["model"]
    vectorizer = recommendation_data["vectorizer"]
    train_df = recommendation_data["df"]
    print("✅ Recommendation model loaded successfully")
except Exception as e:
    print("❌ Error loading recommendation model:", e)
    recommendation_model = None
    vectorizer = None
    train_df = None

# Connect to MongoDB
try:
    client = MongoClient("mongodb+srv://sonalazar:9633591213@cluster0.zs9tqxx.mongodb.net/MainProjectDB?retryWrites=true&w=majority&appName=Cluster0")
    db = client["MainProjectDB"]
    collection = db["products"]
    print("✅ Connected to MongoDB successfully")
except Exception as e:
    print("❌ Error connecting to MongoDB:", e)
    client = None
    db = None
    collection = None

# Add Cart Collection
cart_collection = db["carts"]

# Add to Cart Endpoint
@app.route("/api/cart", methods=["POST"])
def add_to_cart():
    try:
        data = request.json
        user_id = data.get("userId")
        product_id = data.get("productId")
        quantity = int(data.get("quantity", 1))

        if not user_id or not product_id:
            return jsonify({"error": "User ID and Product ID are required"}), 400

        # Check if product exists
        found_product = collection.find_one({"_id": product_id})
        if not found_product:
            return jsonify({"error": "Product not found"}), 404

        # Check if user already has a cart
        cart = cart_collection.find_one({"userId": user_id})

        if cart:
            # Check if product is already in the cart
            product_found = False
            for item in cart["products"]:
                if item["productId"] == product_id:
                    item["quantity"] += quantity
                    product_found = True
                    break

            if not product_found:
                cart["products"].append({"productId": product_id, "quantity": quantity})

            cart_collection.update_one({"userId": user_id}, {"$set": {"products": cart["products"]}})
        else:
            # Create new cart
            new_cart = {
                "userId": user_id,
                "products": [{"productId": product_id, "quantity": quantity}]
            }
            cart_collection.insert_one(new_cart)

        return jsonify({"message": "Product added to cart"}), 200

    except Exception as e:
        print("❌ Error adding to cart:", e)
        return jsonify({"error": str(e)}), 500

# Product Recommendation Endpoint
# Product Recommendation Endpoint
# Product Recommendation Endpoint
@app.route("/api/recommends", methods=["GET"])
def get_recommendations():
    try:
        if collection is None:
            return jsonify({"error": "Database connection unavailable"}), 500

        query = request.args.get("query", "").strip().lower()
        if not query:
            return jsonify({"message": "Query is required"}), 400

        # ✅ Step 1: Check if the query is a disease
        matched_rows = train_df[train_df["Disease"].str.lower() == query]

        # ✅ Step 2: If no direct disease match, check if symptoms match any disease
        if matched_rows.empty:
            matched_rows = train_df[train_df["Symptoms"].str.lower().str.contains(query, na=False)]

        if matched_rows.empty:
            return jsonify({"message": "No recommendations found for this input."}), 404

        # ✅ Extract recommended items from the dataset
        recommended_fruits = matched_rows["Recommended_Fruits"].values[0].split(", ")
        recommended_vegetables = matched_rows["Recommended_Vegetables"].values[0].split(", ")
        recommended_grains = matched_rows["Recommended_Grains"].values[0].split(", ")
        recommended_pulses = matched_rows["Recommended_Pulses"].values[0].split(", ")

        recommended_products = set(recommended_fruits + recommended_vegetables + recommended_grains + recommended_pulses)

        # ✅ Fetch products from MongoDB that match only the recommended items
        products = []
        for product_name in recommended_products:
            found_product = collection.find_one({"product": product_name})  # Fetch only one product per name

            if found_product:
               products.append({
    "id": str(found_product["_id"]),
    "name": found_product.get("product", "Unknown"),
    "category": found_product.get("category", "Unknown"),
    "price": found_product.get("predictedPrice", "N/A"),
    "farmerId": found_product.get("farmerId", "Unknown"),
    "quantity": found_product.get("quantity", 0),
    "inStock": found_product.get("inStock", False),
    "link": f"/buy/{found_product['_id']}"
})

                

        if not products:
            return jsonify({"message": "No matching products found in database."}), 404

        return jsonify({"products": products})

    except Exception as e:
        print("❌ Error in recommendation:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001) 