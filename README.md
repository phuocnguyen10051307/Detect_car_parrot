# Vehicle OCR

Project này được sắp xếp theo 2 phần chính:

- `be/`: backend OCR bằng `FastAPI + PaddleOCR`
- `fe/`: frontend nhận ảnh, upload lên `Cloudinary`, lấy `image_url` rồi gửi sang backend để OCR

Luồng hoạt động:

1. Người dùng chọn ảnh trong frontend
2. Frontend upload ảnh lên Cloudinary
3. Cloudinary trả về `secure_url`
4. Frontend gửi `image_url` sang backend `be`
5. Backend tải ảnh từ URL, OCR, trích xuất thông tin và trả về JSON kết quả

## Cấu trúc thư mục

```text
vehicle-ocr/
|-- be/
|   |-- main.py
|   |-- parser.py
|   |-- requirements.txt
|   |-- test_parser.py
|
|-- fe/
|   |-- index.html
|   |-- app.js
|   |-- style.css
|   |-- server.js
|   |-- package.json
|
|-- dataset/
|   |-- car/
|   |-- dataset.xlsx
|
|-- .env.example
|-- venv/
|-- README.md
```

## Backend `be/`

Backend dùng `FastAPI` và `PaddleOCR`.

Các API hiện có:

- `GET /`
- `POST /ocr`
- `POST /ocr/url`

### Chạy backend

```powershell
cd C:\Users\admin\vehicle-ocr\be
..\venv\Scripts\uvicorn.exe main:app --host 0.0.0.0 --port 8000 --reload
```git bash 
../venv/Scripts/python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```


### Health check backend

```powershell
curl.exe http://127.0.0.1:8000/
```

Kết quả mong đợi:

```json
{"status":"ok"}
```

### OCR bằng upload file trực tiếp

```powershell
curl.exe -X POST "http://127.0.0.1:8000/ocr" -F "file=@..\dataset\car\018.png"
```

### OCR bằng URL ảnh

```powershell
curl.exe -X POST "http://127.0.0.1:8000/ocr/url" -H "Content-Type: application/json" -d "{\"image_url\":\"https://example.com/sample.jpg\"}"
```

### JSON backend trả về

```json
{
  "document_type": "old",
  "card_color": "blue_old",
  "image_url": "https://...",
  "plate": "93A-115.16",
  "engine": "3A92UDY6060",
  "frame": "A13AHH005129",
  "issue_date": "19/04/2018"
}
```

## Frontend `fe/`

Frontend là một trang HTML/CSS/JS đơn giản để:

- chọn ảnh từ máy
- upload ảnh lên Cloudinary
- lấy link ảnh
- gửi link ảnh sang backend `/ocr/url`
- hiển thị kết quả OCR

### Chạy frontend

```powershell
cd C:\Users\admin\vehicle-ocr\fe
node server.js
```

Hoặc:

```powershell
npm start
```

Mở trình duyệt:

```text
http://127.0.0.1:5173
```

### Thông tin cần nhập trên frontend

Bạn chỉ cần nhập:

- `Cloudinary Cloud Name`
- `Cloudinary Upload Preset`

`Backend OCR URL` mặc định đã là:

```text
http://127.0.0.1:8000/ocr/url
```

Nếu backend chạy local đúng cổng `8000` thì không cần sửa ô này.

### Cách dùng frontend

1. Chạy backend
2. Chạy frontend
3. Mở `http://127.0.0.1:5173`
4. Nhập `Cloudinary Cloud Name`
5. Nhập `Cloudinary Upload Preset`
6. Chọn ảnh cà vẹt
7. Bấm `Upload va OCR`

Frontend sẽ:

- upload ảnh lên Cloudinary
- nhận `image_url`
- gọi backend OCR
- hiển thị:
  - link ảnh Cloudinary
  - preview ảnh
  - `document_type`
  - `card_color`
  - `plate`
  - `engine`
  - `frame`
  - `issue_date`

Lưu ý:

- `Upload Preset` nên là preset dạng unsigned nếu upload trực tiếp từ frontend
- frontend có lưu `cloud name`, `upload preset`, `backend url` vào `localStorage`

## Test nhanh toàn bộ hệ thống

### Bước 1: chạy backend

```powershell
cd C:\Users\admin\vehicle-ocr\be
..\venv\Scripts\uvicorn.exe main:app --host 0.0.0.0 --port 8000 --reload
```

### Bước 2: chạy frontend

Mở terminal khác:

```powershell
cd C:\Users\admin\vehicle-ocr\fe
node server.js
```

### Bước 3: mở giao diện

```text
http://127.0.0.1:5173
```

### Bước 4: OCR ảnh mới

Bạn chỉ cần chọn ảnh bất kỳ từ máy rồi bấm `Upload va OCR`.

Không cần chép ảnh vào `dataset/car` khi test qua giao diện.

## Chạy unit test backend

```powershell
cd C:\Users\admin\vehicle-ocr\be
..\venv\Scripts\python.exe -m unittest test_parser.py
```

## Ghi chú

- `be/parser.py` dùng hướng keyword-based, không phụ thuộc line index cố định
- backend hỗ trợ cả OCR theo file upload và OCR theo URL ảnh
- frontend hiện phù hợp để test local nhanh với Cloudinary
- dataset trong `dataset/` dùng cho việc thử nghiệm và benchmark nội bộ
