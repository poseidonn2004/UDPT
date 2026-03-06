Distributed Key-Value Storage System
1. Giới thiệu

Hệ thống này triển khai một Distributed Key-Value Store hoạt động trên nhiều node.
Mỗi node lưu trữ một phần dữ liệu và có cơ chế replication, heartbeat và data recovery để tăng khả năng chịu lỗi.

Hệ thống cho phép thực hiện các thao tác cơ bản:

PUT: lưu key-value

GET: lấy giá trị theo key

DELETE: xóa key

Replica: sao lưu dữ liệu sang các node khác

2. Yêu cầu hệ thống

Cần cài đặt các thành phần sau:

Python 3.9+

pip

Các thư viện Python:

pip install fastapi uvicorn requests
3. Cấu trúc thư mục
│   config.json
│   faststart.ps1
│   server.py
│   start.ps1
│   
├───static
│       index.html
│       style.css
│
└───__pycache__
        server.cpython-314.pyc
4. Cấu hình hệ thống

File config.json định nghĩa các node trong cụm.

Ví dụ:

{
    "self": "http://127.0.0.1:8000",
    "nodes": [
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8001",
        "http://127.0.0.1:8002",
        "http://127.0.0.1:8003",
        "http://127.0.0.1:8004",
        "http://127.0.0.1:8005"
    ]
}

Hệ thống sẽ chạy 6 node trên các port từ 8000 đến 8005.

5. Cách chạy hệ thống
5.1 Chạy từng node

Mỗi node được chạy bằng lệnh:

python server.py 8000

Ví dụ chạy nhiều node:

python server.py 8000
python server.py 8001
python server.py 8002
python server.py 8003
python server.py 8004
python server.py 8005
5.2 Chạy nhiều node bằng script

Có thể chạy tất cả node bằng PowerShell script:

.\start_nodes.ps1

Script sẽ mở nhiều cửa sổ terminal và chạy các node từ 8000 → 8005.

6. Truy cập giao diện hệ thống

Sau khi chạy node:

Mở trình duyệt và truy cập:

http://127.0.0.1:8000

Giao diện web sẽ cho phép thực hiện các thao tác PUT / GET / DELETE.

7. API của hệ thống
7.1 PUT

Lưu key-value

POST /put

Ví dụ:

http://127.0.0.1:8000/put?key=5&value=aaaaa
7.2 GET

Lấy giá trị theo key

GET /get

Ví dụ:

http://127.0.0.1:8000/get?key=5
7.3 DELETE

Xóa key khỏi hệ thống

DELETE /delete

Ví dụ:

http://127.0.0.1:8000/delete?key=5
8. Kiểm thử hệ thống
Test lưu dữ liệu
PUT key=5 value=aaaaa

Hệ thống sẽ:

lưu dữ liệu tại primary node

sao lưu sang 2 replica node

Test node failure

Lưu dữ liệu:

PUT key=5 value=aaaaa

Tắt node primary.

Thực hiện:

GET key=5

Hệ thống sẽ lấy dữ liệu từ replica node.

9. Cơ chế của hệ thống

Hệ thống sử dụng các cơ chế sau:

Consistent Hashing

Key được ánh xạ tới node bằng hàm hash MD5.

Replication

Mỗi key được lưu tại:

1 Primary node

2 Replica node

Heartbeat

Các node gửi request /heartbeat để kiểm tra node còn hoạt động.

Data Recovery

Khi node khởi động lại, node sẽ gọi /snapshot_for để lấy lại dữ liệu cần thiết từ các node khác.
