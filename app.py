from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "running", "name": "Soroush SelfBot API"})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    phone = data.get('phone', '')
    return jsonify({"success": True, "message": f"کد به {phone} ارسال شد"})

@app.route('/api/status')
def status():
    return jsonify({"accounts": [], "active": 0})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
