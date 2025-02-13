from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

ROLIMONS_URL = "https://www.rolimons.com/item/"
LIMITEDS_CACHE = {}  # Cache to store limited values


def scrape_limited_value(item_id):
    """Scrapes the Rolimons page for the value and best price of a limited item."""
    url = f"{ROLIMONS_URL}{item_id}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Error: Status Code {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    value = None
    best_price = None

    # Find all value-stat-data divs
    stat_blocks = soup.find_all("div", class_="value-stat-data")
    headers = soup.find_all("div", class_="value-stat-header")

    for header, data in zip(headers, stat_blocks):
        label = header.text.strip()
        raw_text = data.text.replace(",", "").strip()

        # Check if the extracted text is a valid number
        if raw_text.isdigit():
            price = int(raw_text)

            if label == "Value":
                value = price
            elif label == "Best Price":
                best_price = price
        else:
            print(f"Skipping non-numeric value for {label}: {raw_text}")

    if value is not None or best_price is not None:
        LIMITEDS_CACHE[item_id] = {"value": value, "best_price": best_price}
        return {"value": value, "best_price": best_price}

    return None

@app.route("/get_value/<item_id>", methods=["GET"])
def get_limited_value(item_id):
    """API Endpoint: Returns the limited value and best price of an item."""
    if item_id in LIMITEDS_CACHE:
        return jsonify({"item_id": item_id, **LIMITEDS_CACHE[item_id]})

    result = scrape_limited_value(item_id)
    if result is not None:
        return jsonify({"item_id": item_id, **result})

    return jsonify({"error": "Limited not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True, threaded=True)
