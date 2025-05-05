from flask import Flask, render_template, jsonify, request
import mysql.connector
from wordcloud import WordCloud
import io
import base64
import logging
import re
from collections import Counter
from nltk import ngrams
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Danh sách stopwords tiếng Việt
VIETNAMESE_STOPWORDS = {
    'rất', 'quá', 'cực', 'vô cùng', 'hơi', 'khá', 'tương đối',
    'tốt', 'xấu', 'tệ', 'kém', 'hay', 'dở', 'đẹp', 'xấu',
    'thích', 'ghét', 'yêu', 'chán', 'buồn', 'vui', 'hài lòng',
    'thất vọng', 'tuyệt vời', 'kinh khủng', 'khủng khiếp',
    'đáng giá', 'không đáng', 'đáng tiền', 'lãng phí',
    'này', 'kia', 'đó', 'đây', 'ấy', 'nọ', 'kìa',
    'và', 'hoặc', 'nhưng', 'mà', 'nên', 'vì', 'nếu',
    'thì', 'là', 'của', 'để', 'cho', 'với', 'từ', 'về'
}

def clean_text(text):
    # Chuyển về chữ thường
    text = text.lower()
    
    # Loại bỏ dấu câu và ký tự đặc biệt
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Tách từ
    words = text.split()
    
    # Lọc stopwords
    words = [word for word in words if word not in VIETNAMESE_STOPWORDS]
    
    return ' '.join(words)

def get_word_frequencies(text, n=2):
    # Tạo bigrams (cụm 2 từ)
    bigrams = list(ngrams(text.split(), n))
    
    # Chuẩn hóa thứ tự từ trong mỗi bigram
    normalized_bigrams = []
    for bigram in bigrams:
        # Sắp xếp các từ trong bigram để đảm bảo thứ tự nhất quán
        sorted_bigram = tuple(sorted(bigram))
        normalized_bigrams.append(sorted_bigram)
    
    # Đếm tần suất
    freq = Counter(normalized_bigrams)
    
    # Gộp các bigram có cùng từ nhưng khác thứ tự
    merged_freq = {}
    for bigram, count in freq.items():
        # Chuyển bigram thành string và sắp xếp các từ
        key = ' '.join(sorted(bigram))
        if key in merged_freq:
            merged_freq[key] += count
        else:
            merged_freq[key] = count
    
    # Sắp xếp theo tần suất giảm dần và lấy top 20
    sorted_freq = dict(sorted(merged_freq.items(), key=lambda x: x[1], reverse=True)[:20])
    
    return sorted_freq

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

def get_wordcloud_data(sentiment=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Query để lấy reviews dựa trên sentiment
        if sentiment:
            query = "SELECT review_text FROM reviews WHERE sentiment = %s"
            cursor.execute(query, (sentiment,))
        else:
            query = "SELECT review_text FROM reviews"
            cursor.execute(query)
            
        reviews = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Kết hợp và làm sạch tất cả reviews
        all_text = ' '.join([review[0] for review in reviews])
        cleaned_text = clean_text(all_text)
        
        # Lấy tần suất từ
        word_freq = get_word_frequencies(cleaned_text)
        
        # Tạo wordcloud với các tùy chỉnh
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            max_words=100,
            contour_width=3,
            contour_color='steelblue',
            min_font_size=10,
            max_font_size=100,
            relative_scaling=0.5,
            collocations=True,  # Cho phép cụm từ
            prefer_horizontal=0.7,  # Ưu tiên hiển thị ngang
            regexp=r"\w[\w' ]+",  # Regex để bắt cụm từ
            normalize_plurals=False
        ).generate_from_frequencies(word_freq)
        
        # Chuyển đổi wordcloud thành base64 string
        img = io.BytesIO()
        wordcloud.to_image().save(img, 'PNG')
        img.seek(0)
        img_str = base64.b64encode(img.getvalue()).decode()
        
        # Trả về cả hình ảnh và dữ liệu tần suất
        return {
            'image': img_str,
            'frequencies': word_freq
        }
    except Exception as e:
        logging.error(f"Error generating wordcloud: {str(e)}")
        return None

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/get_wordcloud')
def get_wordcloud():
    sentiment = request.args.get('sentiment')
    result = get_wordcloud_data(sentiment)
    if result:
        return jsonify(result)
    return jsonify({'error': 'Failed to generate wordcloud'}), 500

@app.route('/get_reviews')
def get_reviews():
    try:
        sentiment = request.args.get('sentiment')
        conn = get_connection()
        cursor = conn.cursor()
        
        if sentiment:
            query = "SELECT author, review_text, confidence FROM reviews WHERE sentiment = %s ORDER BY id DESC"
            cursor.execute(query, (sentiment,))
        else:
            query = "SELECT author, review_text, confidence FROM reviews ORDER BY id DESC"
            cursor.execute(query)
            
        reviews = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Chuyển đổi kết quả thành list of dicts
        reviews_list = [
            {
                'author': review[0],
                'text': review[1],
                'confidence': f"{float(review[2]) * 100:.1f}%"
            }
            for review in reviews
        ]
        
        return jsonify({'reviews': reviews_list})
    except Exception as e:
        logging.error(f"Error fetching reviews: {str(e)}")
        return jsonify({'error': 'Failed to fetch reviews'}), 500

@app.route('/get_sentiment_stats')
def get_sentiment_stats():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Đếm số lượng đánh giá cho mỗi loại sentiment
        query = """
            SELECT 
                SUM(CASE WHEN sentiment = 'Tích cực' THEN 1 ELSE 0 END) as positive,
                SUM(CASE WHEN sentiment = 'Tiêu cực' THEN 1 ELSE 0 END) as negative
            FROM reviews
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        stats = {
            'positive': result[0] or 0,
            'negative': result[1] or 0
        }
        
        cursor.close()
        conn.close()
        
        return jsonify(stats)
        
    except Exception as e:
        logging.error(f"Error getting sentiment stats: {str(e)}")
        return jsonify({
            'error': 'Lỗi khi lấy thống kê',
            'positive': 0,
            'negative': 0
        }), 500

if __name__ == '__main__':
    print("Dashboard server starting... Access the dashboard at http://127.0.0.1:5001")
    app.run(debug=True, port=5001) 