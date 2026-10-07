# Hướng dẫn hoàn thành bài lab Day 6 — 3D from Point Clouds & LiDAR-Camera Projection

Tài liệu này là bản tóm tắt thực tế để bạn hoàn thành bài lab nhanh và đúng yêu cầu của repo. Mục tiêu là giúp bạn không bỏ sót checkpoint, không quên file kết quả, và có một bài báo cáo đúng cấu trúc để nộp.

## 1. Chọn topic nên làm

Nếu bạn muốn hoàn thành bài lab với rủi ro thấp nhất, nên chọn:

- Topic A: LiDAR-camera projection QA
- Dataset gợi ý: `data/synthetic` để debug, `data/kitti_mini` để benchmark chính

Vì:
- Repo đã có sẵn code skeleton trong `starter/projection.py`.
- Cần viết đúng 2 hàm TODO (`velo_to_cam`, `cam_to_image`).
- Dễ tạo ảnh overlay và perturb calibration để làm benchmark.
- Dễ tạo failure case bằng cách xoay yaw hoặc dịch LiDAR.
- Không cần GPU, dễ chạy được trong thời gian 2 giờ.

## 2. Mục tiêu bài lab cần đạt

Bạn cần có đủ 5 sản phẩm bắt buộc:

1. Claim kỹ thuật rõ ràng
2. Bảng số liệu/plot từ thí nghiệm
3. Demo ảnh/video chạy thật
4. Failure case minh hoạ và giải thích
5. Khuyến nghị triển khai thực tế

Ngoài ra, cần có:

- `starter/projection.py` đã làm xong phần `TODO(CP2)`
- `src/` chứa code tự viết
- `results/` chứa CSV và ảnh
- `report/REPORT.md` đúng template

## 3. Checklist thực hiện theo checkpoint

### CP0 — Chuẩn bị trước buổi học

Yêu cầu:

- Fork repo theo tên: `<HoVaTen>-<MSSV>-Track4-Day21`
- Clone repo về máy
- Tạo môi trường Python
- Cài đặt package từ `requirements.txt`
- Chạy kiểm tra dữ liệu:

```bash
python tools/verify_data.py --data-root data/kitti_mini
python tools/verify_data.py --data-root data/nuscenes_mini_subset
```

- Kiểm tra health data:

```bash
python -m starter.data_health --data-root data/synthetic
```

Kết quả mong đợi:
- Có file `results/data_health.csv`
- In ra 5 frame `000000` đến `000004`

### CP1 — Chọn topic và viết claim

Với topic A, ví dụ claim tốt là:

> "Lệch yaw 1° làm tăng đáng kể tỷ lệ điểm LiDAR rơi ngoài khung hình và giảm số điểm nằm trong 2D box của đối tượng ở khoảng cách > 30m; sai lệch > 2° sẽ tạo ra lỗi projection rõ ràng trên cả dữ liệu synthetic và KITTI."

Bạn cần ghi claim này vào `report/REPORT.md` mục 1.

### CP2 — Viết TODO trong `starter/projection.py`

Hãy mở file:

- `starter/projection.py`

Viết hai hàm:

- `velo_to_cam(points_xyz, calib)`
- `cam_to_image(points_cam, P2, image_shape, min_depth=0.1)`

Đúng logic cần làm:

- `velo_to_cam`:
  - Chuyển điểm về dạng đồng nhất (N,4)
  - Nhân với `calib.T_cam_velo`
  - Trả về 3 cột đầu

- `cam_to_image`:
  - Lọc điểm NaN/Inf
  - Chuyển sang dạng đồng nhất
  - Nhân với `P2`
  - Chia cho `s` để thu được `u, v`
  - Chỉ giữ điểm `depth > min_depth`
  - Giữ điểm trong khung hình `(0 <= u < W, 0 <= v < H)`

Chạy thử:

```bash
python -m starter.projection --data-root data/synthetic --frame 000000
python -m starter.projection --data-root data/kitti_mini --frame 000011
python -m starter.projection --data-root data/nuscenes_mini_subset --frame scene-0103_010
```

Kết quả mong đợi:
- Có ảnh overlay trong `results/figures/`
- Điểm LiDAR nằm khớp trên xe, người, cột và mặt đường
- Không có điểm lệch lên bầu trời

### CP3 — Benchmark chính

Với topic A, thí nghiệm đơn giản và mạnh là đo độ nhạy theo yaw drift.

Ví dụ cấu hình:

- yaw = 0°, 0.5°, 1°, 2°, 3°
- trên cùng 1 frame, ví dụ `data/kitti_mini` frame `000011`
- Metric: `% điểm nằm trong ảnh`, `% điểm nằm trong 2D box`, hoặc số điểm rơi ngoài box

Bạn nên ghi kết quả ra CSV, ví dụ:

```bash
results/yaw_perturb_sweep.csv
```

Ví dụ format:

```csv
yaw_deg,inside_image_ratio,points_in_box_ratio,mean_depth
0.0,0.92,0.78,12.5
0.5,0.91,0.74,12.6
1.0,0.88,0.62,12.7
2.0,0.73,0.41,13.1
3.0,0.58,0.24,13.8
```

Bạn có thể tạo script trong `src/` như:

- `src/benchmark_projection.py`
- `src/plot_projection_sweep.py`

Lưu ý:
- Cố định `seed` nếu dùng random
- Chỉ thay đổi một yếu tố: yaw drift
- Dùng cùng frame và cùng dữ liệu

### CP4 — Failure case

Tạo ảnh fail rõ ràng bằng cách tăng yaw hoặc dịch LiDAR.

Ví dụ:

```bash
python -m starter.projection --data-root data/kitti_mini --frame 000011 --yaw-deg 3.0
```

Tạo ảnh fail theo tên ví dụ:

- `results/figures/fail_01_yaw_3deg.png`

Giải thích failure case:

- Lỗi thuộc lớp: Geometry
- Nguyên nhân: extrinsic sai, LiDAR và camera lệch góc; điểm dịch chuyển, đẩy ra ngoài box hoặc lên bầu trời
- Khi nào sai: khi calibration drift lớn hơn ngưỡng, đặc biệt ở khoảng cách xa

### CP5 — Khuyến nghị triểnploi

Trong báo cáo, phần 4 cần nói rõ:

- Use case: ADAS / robot / drone
- Đánh đổi: tốc độ - độ chính xác - tài nguyên
- Chỉ số cần monitor khi chạy thật:
  - tỷ lệ điểm trong khung hình
  - số điểm nằm trong box
  - calibration drift estimate
  - số frame lỗi liên tiếp

### CP6 — Demo và báo cáo cuối cùng

Trước khi nộp:

```bash
python tools/check_submission.py
```

Kết quả cuối cùng phải có dòng:

```text
KẾT QUẢ: SẴN SÀNG NỘP
```

Tất cả các dòng phải là `[PASS]`.

## 4. Cấu trúc repo bắt buộc

Bố cục tối thiểu cần có:

```text
<HoVaTen>-<MSSV>-Track4-Day21/
├── src/
├── starter/projection.py
├── results/
│   ├── <thí_nghiệm>.csv
│   └── figures/
│       ├── <demo>.png
│       └── fail_<số>_<mô_tả>.png
├── report/
│   └── REPORT.md
└── README.md, RUBRIC.md, ...
```

## 5. Gợi ý script bạn nên tạo trong `src/`

Các file nên có dạng:

- `src/benchmark_projection.py`
  - load frame
  - loop các mức yaw
  - tính metric
  - lưu CSV

- `src/plot_projection.py`
  - đọc CSV
  - vẽ line plot hoặc bar chart
  - lưu PNG

- `src/failure_case_demo.py`
  - chạy 1 frame với yaw drift lớn
  - lưu ảnh fail

Ví dụ đầu vào cho benchmark:

```python
import numpy as np

for yaw in [0.0, 0.5, 1.0, 2.0, 3.0]:
    calib = perturb_extrinsic(fr["calib"], yaw_deg=yaw)
    uv, depth, mask = project_velo_to_image(fr["points"], calib, fr["image"].shape)
    # tính tỷ lệ điểm nằm trong box, ảnh, v.v.
```

## 6. Mẫu báo cáo `report/REPORT.md`

Bạn có thể dùng mẫu dưới đây, điền đầy đủ và bỏ những phần `[ĐIỀN]`.

```md
# REPORT - Day 6 Lab

- Họ tên: [ĐIỀN]
- MSSV: [ĐIỀN]
- Lớp: [ĐIỀN]
- Topic: A
- Dataset: data/kitti_mini / data/synthetic
- Link repo: [ĐIỀN]
- Link video (nếu có): [ĐIỀN]
- AI usage: [ĐIỀN]

## 1. Claim

Lệch yaw 1° làm tăng đáng kể tỷ lệ điểm LiDAR rơi ngoài khung hình và giảm số điểm nằm trong 2D box của đối tượng ở khoảng cách > 30 m trên frame KITTI 000011.

## 2. Benchmark / số liệu

- Dataset: data/kitti_mini, frame 000011
- Điều kiện: cùng frame, cùng điểm cloud, chỉ thay đổi yaw
- Mức thay đổi: 0°, 0.5°, 1°, 2°, 3°
- Metric: % điểm trong ảnh, % điểm trong 2D box

| yaw_deg | inside_image_ratio | points_in_box_ratio |
|---|---:|---:|
| 0.0 | 0.92 | 0.78 |
| 0.5 | 0.91 | 0.74 |
| 1.0 | 0.88 | 0.62 |
| 2.0 | 0.73 | 0.41 |
| 3.0 | 0.58 | 0.24 |

Biểu đồ/ảnh: `results/figures/yaw_sweep.png`

## 3. Failure case

- Failure case: `fail_01_yaw_3deg.png`
- Lỗi: Geometry / calibration drift
- Khi nào sai: khi yaw drift > 2° hoặc khi đối tượng ở khoảng cách xa
- Vì sao: ma trận extrinsic bị lệch, điểm LiDAR chiếu sai vị trí trên ảnh
- Cách phát hiện: so sánh % điểm nằm trong box hoặc số điểm trong ảnh giảm đột ngột

## 4. Liên hệ thực tế

Trong hệ thống ADAS, lệch calibration của LiDAR-camera là sự cố nguy hiểm vì có thể làm tệ đi độ chính xác của nhận diện và vị trí đối tượng. Với robot hoặc drone, sai lệch nhỏ cũng tạo ra lỗi trong dò chướng ngại vật. Hệ thống cần theo dõi các chỉ số: tỷ lệ điểm trong khung hình, số điểm/box mismatch, độ lệch extrinsic ước tính, và cảnh báo khi nhiều frame liên tiếp báo lỗi.

## 5. Cách chạy lại

```bash
python -m starter.projection --data-root data/synthetic --frame 000000
python -m starter.projection --data-root data/kitti_mini --frame 000011
python -m starter.projection --data-root data/kitti_mini --frame 000011 --yaw-deg 3.0
python -m src.benchmark_projection
```

## 6. Kết luận

Calibration LiDAR-camera là yếu tố cực kỳ quan trọng: chỉ một góc lệch nhỏ cũng làm sai lệch vị trí chiếu điểm trên ảnh, nhất là ở đối tượng xa. Vì vậy, cần kiểm tra định kỳ và có metric tự động phát hiện sự lệch trước khi model fail.
```

## 7. Lưu ý khi nộp

Trước khi nộp, chạy:

```bash
python tools/check_submission.py
```

Nếu mọi thứ đúng, bạn sẽ thấy:

- `[PASS]` cho từng mục
- `KẾT QUẢ: SẴN SÀNG NỘP`

Nếu chưa chạy đúng, hãy kiểm tra lại:
- `report/REPORT.md` không còn `[ĐIỀN]`
- `results/` có CSV + ảnh demo + ảnh fail
- Kích thước file không quá 20 MB
- Không có API key / token
- Không có file dữ liệu mới ngoài `data/`

## 8. Gợi ý tiết kiệm thời gian

Nếu bạn đang thiếu thời gian, làm theo thứ tự này:

1. Sửa `starter/projection.py`
2. Chạy `python -m starter.projection --data-root data/synthetic --frame 000000`
3. Chạy benchmark trên `data/kitti_mini`
4. Chụp ảnh fail bằng `--yaw-deg 3.0`
5. Viết `report/REPORT.md`
6. Chạy `python tools/check_submission.py`

## 9. Kết luận ngắn

Nếu bạn chọn Topic A, đây là đề bài dễ triển khai nhất và đủ tiêu chí điểm cao nếu bạn:

- làm đúng code projection,
- có benchmark 3 mức,
- có ảnh fail rõ ràng,
- viết báo cáo chặt chẽ và đúng template.

Đây là hướng đi an toàn nhất để hoàn thành bài lab trong 2 giờ.
