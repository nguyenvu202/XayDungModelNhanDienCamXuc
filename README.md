# Chatbot và Hệ thống Đánh giá Sản phẩm

Ứng dụng web kết hợp chatbot AI và hệ thống phân tích cảm xúc đánh giá sản phẩm.

## Yêu cầu hệ thống

- Python 3.12.7
- MySQL Server
- Ollama (cho chatbot AI)

## Cài đặt

1. **Clone repository**:
```bash
git clone <repository-url>
cd <project-directory>
```

2. **Tạo môi trường ảo Python**:
```bash
python -m venv venv
```

3. **Kích hoạt môi trường ảo**:
- Windows:
```bash
venv\Scripts\activate
```

1. **Cài đặt các thư viện Python**:
```bash
pip install 
```

## Các thư viện cần thiết

```
flask
mysql.connector
tensorflow
numpy
flask_cors
wordcloud
nltk
```
- Nếu gặp lỗi "Authentication plugin 'caching_sha2_password' is not supported", chạy lệnh:
```bash
pip install mysql-connector-python --upgrade
```

## Cấu hình Database

1. **MySQL Database**:
```sql
CREATE DATABASE IF NOT EXISTS Store;
USE Store;

CREATE TABLE IF NOT EXISTS reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    author VARCHAR(255) NOT NULL,
    review_text TEXT NOT NULL,
    sentiment VARCHAR(50) NOT NULL,
    confidence FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
## Cấu hình Ollama

1. Cài đặt Ollama từ [ollama.ai](https://ollama.ai)
2. Tải model llama3.1:8b:
```bash
ollama pull llama3.1:8b
```

## Cấu trúc thư mục

```
project/
├── app.py                  # Server chính cho chatbot và phân tích đánh giá
├── dashboard_server.py     # Server cho dashboard phân tích
├── requirements.txt        # Danh sách các thư viện cần thiết
├── README.md              # Tài liệu hướng dẫn
├── Model/                 # Thư mục chứa model và tokenizer
│   ├── model_cnn_bilstm.h5
│   └── tokenizer_data.pkl
├── static/               # Thư mục chứa tài nguyên tĩnh
│   └── image/           # Hình ảnh và assets
└── templates/           # Thư mục chứa các file HTML
    ├── index.html      # Trang chủ với chatbot
    └── dashboard.html  # Trang dashboard phân tích
```

## Chạy ứng dụng

1. **Chạy ứng dụng Flask**:
```bash
python app.py
```

1. Truy cập ứng dụng tại: `http://localhost:5000`

## Tính năng

1. **Chatbot AI**:
- Tư vấn sản phẩm
- Trả lời câu hỏi
- Lưu lịch sử chat

2. **Hệ thống đánh giá**:
- Phân tích cảm xúc đánh giá
- Lưu trữ đánh giá
- Hiển thị kết quả phân tích

## Xử lý lỗi thường gặp

1. **Lỗi kết nối MySQL**:
- Kiểm tra MySQL Server đang chạy
- Kiểm tra thông tin đăng nhập trong `app.py`
- Nếu gặp lỗi "Authentication plugin 'caching_sha2_password' is not supported", chạy lệnh:
```bash
pip install mysql-connector-python --upgrade
```

2. **Lỗi Ollama**:
- Kiểm tra Ollama đang chạy
- Kiểm tra model đã được tải

3. **Lỗi Model**:
- Kiểm tra file model và tokenizer tồn tại
- Kiểm tra phiên bản TensorFlow

## Đóng góp

Mọi đóng góp đều được hoan nghênh. Vui lòng tạo issue hoặc pull request.
