# Báo cáo Day 6: Độ nhạy của phép chiếu LiDAR-camera với lệch yaw

> Trạng thái: hoàn thành CP3 (15 cấu hình, 60 dòng kết quả object, CSV tái lập). Phân tích failure và báo cáo cuối sẽ hoàn thiện ở CP4–CP5.

- **Họ tên:** Nguyễn Văn Tứ
- **MSSV:** 2A202602586
- **Lớp:** AI20K-H209
- **Link repo:** https://github.com/nguyenvantu19/NguyenVanTu-2A202602586-Track4-Day21
- **Topic:** A — Kiểm tra calibration LiDAR-camera bằng projection (LiDAR-camera projection QA), mục tiêu mức Good; chạy CPU, không cần detector.
- **Dataset:** `data/synthetic` để debug; `data/kitti_mini` cho thí nghiệm chính. Nguồn dữ liệu thật: KITTI Vision Benchmark Suite.
- **Các frame đã kiểm tra dữ liệu và sẽ dùng:** synthetic `000000`, `000001`, `000002`, `000003`, `000004`; KITTI `000019`, `000011`, `000004`.
- **Vai trò frame KITTI:** `000019` có Truck gần (z_cam = 5,46 m); `000011` có Car ở 26,64 m và nhiều Pedestrian; `000004` có Car xa ở 51,17 m. Các khoảng cách này là độ sâu tâm đáy box theo label, không phải khoảng cách Euclid.

> Hãy viết ngắn: mỗi mục từ 3 đến 8 dòng, ưu tiên số liệu và hình ảnh.

## 1. Claim

**Claim giả thuyết:** Trên từng frame KITTI `000019`, `000011`, `000004`, khi chỉ làm lệch yaw của extrinsic LiDAR-camera +1° quanh trục z của LiDAR, trung vị độ dịch chuyển pixel của cùng tập điểm LiDAR so với calibration gốc sẽ lớn hơn 10 pixel.

**Kết quả CP3:** Claim được số liệu hỗ trợ trên cả 3 frame: trung vị tại +1° lần lượt 14,728 / 14,601 / 14,778 px. Đây là độ nhạy so với calibration gốc, chưa phải sai số so với correspondence pixel ground truth độc lập.

- **Phép đo:** `d_i = sqrt((u_i(yaw) - u_i(0))² + (v_i(yaw) - v_i(0))²)`; báo `median(d_i)` theo từng frame, so ngưỡng 10 px ở +1°; chỉ cần một frame không vượt ngưỡng là claim bị bác bỏ.
- **Tập điểm cố định:** điểm có cả 4 giá trị hữu hạn, khoảng cách Euclid XYZ 3–80 m, z_cam > 0,1 m và nằm trong ảnh ở baseline 0°. Giữ nguyên ID điểm qua mọi mức; điểm ra ngoài ảnh sau perturb vẫn tính độ dịch chuyển nếu phép chiếu hữu hạn và depth dương; báo riêng số điểm không chiếu được.
- **Các mức thay đổi:** yaw `0°, +0,5°, +1°, +2°, +3°` bằng `perturb_extrinsic`; giữ pitch, roll và translation bằng 0, giữ nguyên ảnh, P2, R0_rect, point cloud và bộ lọc. Không lấy mẫu ngẫu nhiên.
- **Metric bổ sung cho mức Good:** % điểm trong FOV trên tổng điểm hữu hạn; % điểm của từng object còn chiếu vào đúng 2D box GT. Tập điểm object xác định bằng 3D box GT ở calibration gốc, giữ cố định qua sweep; xét Car/Van/Truck/Pedestrian, bỏ DontCare và báo số điểm làm mẫu số.
- **Kiểm tra data health trước thí nghiệm:** `results/data_health.csv` có invalid_ratio khoảng 0,096–0,100% ở cả 5 frame synthetic; frame `000003` có 22.063 điểm, thấp hơn các frame còn lại (23.760–23.953 điểm). Ba frame KITTI đã đọc thành công, lần lượt có 115.697 / 108.004 / 115.976 điểm, invalid_ratio = 0; chưa suy ra calibration đúng chỉ từ các thống kê này.
- **Câu trình bày CP1:** Tôi đo độ dịch chuyển pixel và tỉ lệ điểm trong FOV/box trên KITTI `000019`, `000011`, `000004` khi thay đổi yaw ở 5 mức từ 0° đến 3°; ngưỡng 10 px là giả thuyết cần kiểm chứng ở CP3.

## 2. Evidence

CP2: kiểm tra điểm synthetic `(10, 0, 0)` cho z_cam = 9,72732 m, pixel `(613,964; 175,007)`; kiểm tra NaN/Inf, depth, biên ảnh, đầu vào rỗng và cột tịnh tiến của P2 đều đạt.
Ba baseline KITTI `000019`, `000011`, `000004` có lần lượt 18.792 / 19.946 / 19.063 điểm trong ảnh. Sweep giữ cố định ID điểm; không có điểm tham chiếu nào mất khả năng chiếu ở 15 cấu hình. Hai lần chạy cho SHA256 của cả hai CSV giống hệt nhau, không lấy mẫu ngẫu nhiên.

| Yaw (°) | Median 000019 (px) | Median 000011 (px) | Median 000004 (px) | FOV 000004 (%) | Object trong box 000004 (%) |
|---|---:|---:|---:|---:|---:|
| 0 | 0,000 | 0,000 | 0,000 | 16,437 | 100,000 |
| 0,5 | 7,365 | 7,297 | 7,388 | 16,428 | 94,175 |
| 1 | 14,728 | 14,601 | 14,778 | 16,410 | 79,612 |
| 2 | 29,447 | 29,239 | 29,556 | 16,361 | 54,369 |
| 3 | 44,141 | 43,895 | 44,341 | 16,353 | 20,388 |

Số liệu đầy đủ: [yaw_perturb_sweep.csv](../results/yaw_perturb_sweep.csv), [yaw_object_sweep.csv](../results/yaw_object_sweep.csv); cấu hình/phiên bản thư viện: [experiment_config.json](../results/experiment_config.json). FOV dùng toàn bộ điểm XYZI hữu hạn; metric object dùng tổng số điểm trong từng 3D box ở baseline làm mẫu số, gồm cả điểm ngoài ảnh. Tỷ lệ baseline thấp ở `000011` chịu ảnh hưởng của Car truncation = 0,98; cần xem từng object thay vì kết luận calibration lỗi từ số tổng hợp.

![benchmark yaw](../results/figures/yaw_sweep.png)

![demo KITTI 000011](../results/figures/overlay_000011_r0.0_p0.0_y0.0_t0.0_0.0_0.0.png)

Baseline gần: [000019](../results/figures/overlay_000019_r0.0_p0.0_y0.0_t0.0_0.0_0.0.png); xa: [000004](../results/figures/overlay_000004_r0.0_p0.0_y0.0_t0.0_0.0_0.0.png). Nguồn ảnh: KITTI Vision Benchmark Suite.

## 3. Failure case

Nêu khi nào hệ thống hoặc phương pháp fail, vì sao fail, và liên hệ tới lớp nào trong 6 lớp debug: I/O, Geometry, Time, Preprocess, Model, Metric.

![failure](../results/figures/fail_[ĐIỀN].png)

[ĐIỀN]

## 4. Khuyến nghị nếu triển khai thật

Use-case cụ thể (ADAS / robot / drone), trade-off và bước tiếp theo.

[ĐIỀN]

## 5. Cách chạy lại

Các lệnh kiểm tra dữ liệu phục vụ CP1, chạy từ thư mục gốc repo sau khi kích hoạt `.venv`. Lệnh tái tạo overlay và benchmark sẽ được bổ sung ở CP2–CP3.

```bash
python -m starter.data_health --data-root data/synthetic --out results/data_health.csv
python -m starter.data_health --data-root data/kitti_mini --out results/data_health_kitti.csv
python -m src.validate_projection
python -m starter.projection --data-root data/synthetic --frame 000000
python -m starter.projection --data-root data/kitti_mini --frame 000019
python -m starter.projection --data-root data/kitti_mini --frame 000011
python -m starter.projection --data-root data/kitti_mini --frame 000004
python -m starter.projection --data-root data/nuscenes_mini_subset --frame scene-0103_010
python -m src.benchmark_projection
```

## 6. Khai báo sử dụng AI

Ghi rõ đã dùng công cụ AI nào, dùng vào việc gì, và bạn đã tự kiểm chứng kết quả đó bằng cách nào. Nếu không dùng AI, ghi "Không sử dụng". Xem quy định ở `RULES.md` mục 2.

| Công cụ | Dùng cho việc gì | Bạn đã kiểm chứng thế nào |
|---|---|---|
| OpenAI Codex | Đọc tài liệu lab, đề xuất topic A, chọn frame và soạn claim/kế hoạch đo cho CP1. | Codex đã dùng `load_frame` để kiểm tra ảnh, điểm, calibration và label của các frame đã chọn; tính lại `point_stats` và đối chiếu số điểm/invalid_ratio của 3 frame KITTI với CSV CP0. Học viên cần tự đọc lại định nghĩa metric và kiểm chứng claim bằng benchmark ở CP3; chưa có số liệu chứng minh claim. |
