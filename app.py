# MySQL connection
def get_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password="nguyenvu",
            database="Store"
        )
        return conn
    except mysql.connector.Error as err:
        logging.error(f"MySQL Connection Error: {err}")
        raise
import logging
import traceback
from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for, flash
import mysql.connector
import tensorflow as tf
from tensorflow.keras.preprocessing.text import text_to_word_sequence
from tensorflow.keras.preprocessing.sequence import pad_sequences
import pickle
import numpy as np
import os
from flask_cors import CORS
import requests
import json
from datetime import datetime
import sqlite3

app = Flask(__name__)
CORS(app)

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Global variables for model and tokenizer
my_model = None
my_tokenizer = None

# Load model and tokenizer
def load_model_and_tokenizer():
    global my_model, my_tokenizer
    try:
        # Check if model file exists
        if not os.path.exists('model/model_cnn_bilstm.h5'):
            logging.error("Model file not found at 'model/model_cnn_bilstm.h5'")
            return False
            
        # Check if tokenizer file exists
        if not os.path.exists('model/tokenizer_data.pkl'):
            logging.error("Tokenizer file not found at 'model/tokenizer_data.pkl'")
            return False
            
        # Load model
        my_model = tf.keras.models.load_model('model/model_cnn_bilstm.h5')
        
        # Load tokenizer
        with open('model/tokenizer_data.pkl', 'rb') as handle:
            my_tokenizer = pickle.load(handle)
            
        logging.info("Model and tokenizer loaded successfully")
        return True
        
    except Exception as e:
        logging.error(f"Error loading model or tokenizer: {str(e)}")
        logging.error(traceback.format_exc())
        return False

# Try to load model and tokenizer at startup
if not load_model_and_tokenizer():
    logging.warning("Failed to load model and tokenizer. Sentiment analysis will not be available.")

# Text preprocessing and prediction functions
def preprocess_raw_input(raw_input, tokenizer):
    try:
        # Chuyển đổi văn bản thành danh sách từ
        input_text_pre = list(text_to_word_sequence(raw_input))
        input_text_pre = " ".join(input_text_pre)

        # Tokenize văn bản đầu vào
        tokenized_data_text = tokenizer.texts_to_sequences([input_text_pre])

        # Đệm chuỗi để đảm bảo độ dài cố định (maxlen=512 từ code mẫu)
        vec_data = pad_sequences(tokenized_data_text, padding="post", maxlen=512)
        
        return vec_data
    except Exception as e:
        logging.error(f"Error preprocessing text: {str(e)}")
        logging.error(traceback.format_exc())
        raise

def inference_model(input_feature, model):
    try:
        # Dự đoán đầu ra từ mô hình
        output = model(input_feature).numpy()[0]

        # Lấy chỉ mục của lớp có giá trị cao nhất
        result = np.argmax(output)

        # Ánh xạ chỉ mục sang nhãn
        label_dict = {0: "Tiêu cực", 1: "Trung lập", 2: "Tích cực"}
        label = label_dict[result]

        return label, float(np.max(output))
    except Exception as e:
        logging.error(f"Error in model inference: {str(e)}")
        logging.error(traceback.format_exc())
        raise

def predict_sentiment(raw_input):
    try:
        # Tiền xử lý dữ liệu đầu vào
        input_model = preprocess_raw_input(raw_input, my_tokenizer)

        # Dự đoán kết quả
        sentiment, confidence = inference_model(input_model, my_model)
        
        logging.debug(f"Sentiment prediction for text: '{raw_input}' => {sentiment} (confidence: {confidence:.2f})")
        
        return sentiment, confidence
    except Exception as e:
        logging.error(f"Error predicting sentiment: {str(e)}")
        logging.error(traceback.format_exc())
        return "Không xác định", 0.0

@app.route('/')
def index():
    return render_template('index.html', title="Hệ thống đánh giá")

@app.route('/submit_review', methods=['POST'])
def submit_review():
    try:
        # Get form data and log all received data
        logging.debug(f"Form data received: {request.form}")
        
        author = request.form.get('author', '')
        review_text = request.form.get('reviewText', '')
        
        logging.debug(f"Extracted author: '{author}', review_text: '{review_text}'")
        
        if not author or not review_text:
            logging.warning("Missing required form fields")
            response = jsonify({
                'error': 'Missing required fields', 
                'details': 'Author and review text are required'
            })
            logging.debug(f"Sending response: {response.data}")
            return response, 400
        
        # Predict sentiment with new function
        sentiment, confidence = predict_sentiment(review_text)
        
        # Log received data for debugging
        logging.debug(f"Received review from {author}: {review_text}, Predicted sentiment: {sentiment}, confidence: {confidence:.2f}")
        
        try:
            # Insert review into database - add confidence column
            conn = get_connection()
            cursor = conn.cursor()
            
            # Check if confidence column exists, if not add it
            try:
                cursor.execute("SHOW COLUMNS FROM reviews LIKE 'confidence'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE reviews ADD COLUMN confidence FLOAT DEFAULT 0")
                    logging.info("Added confidence column to reviews table")
            except Exception as col_err:
                logging.warning(f"Could not check/add confidence column: {str(col_err)}")
            
            # Insert review with confidence value
            query = "INSERT INTO reviews (author, review_text, sentiment, confidence) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (author, review_text, sentiment, float(confidence)))
            conn.commit()
            cursor.close()
            conn.close()
            logging.debug("Database insert successful")
        except mysql.connector.Error as db_err:
            logging.error(f"Database error: {str(db_err)}")
            logging.error(traceback.format_exc())
            response = jsonify({
                'error': 'Lỗi cơ sở dữ liệu', 
                'details': str(db_err)
            })
            logging.debug(f"Sending response: {response.data}")
            return response, 500
        
        # Format confidence as percentage
        confidence_percent = f"{confidence * 100:.1f}%"
        
        # Return success response with sentiment and confidence
        response = jsonify({
            'message': 'Đánh giá đã được gửi thành công!', 
            'sentiment': sentiment,
            'confidence': confidence_percent
        })
        logging.debug(f"Sending success response: {response.data}")
        return response, 200
    
    except Exception as e:
        # Log detailed error with traceback
        error_msg = f"Unexpected error: {str(e)}"
        logging.error(error_msg)
        logging.error(traceback.format_exc())
        
        # Return error response as JSON
        response = jsonify({
            'error': 'Không thể gửi đánh giá', 
            'details': str(e)
        })
        logging.debug(f"Sending error response: {response.data}")
        return response, 500

# Serve static files
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    # Ensure templates folder exists
    os.makedirs('templates', exist_ok=True)
    print("Server starting... Access the application at http://127.0.0.1:5000")
    app.run(debug=True)