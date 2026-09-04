from flask import Flask, request, jsonify
app = Flask(__name__)

#加载训练好的模型
rf_model = joblib.load("rf_model.pkl")
scaler = joblib.load("scaler.pkl")

@app.route("/api/detect",methods=["POST"])
def detect_api():
    """缺陷检测接口，对应PPT13个REST接口之一"""
    file = request.files["image"]
    file.save("tmp.jpg")
    gray,edges = preprocess_pipeline("tmp.jpg")
    feat = extract_features(gray,edges)
    feat_s = scaler.transform(feat)
    pred = rf_model.predict(feat_s)
    return jsonify({"defect_class":int(pred[0])})

if __name__ == "__main__":
    app.run(debug=True)