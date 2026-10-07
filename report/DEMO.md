# Chuẩn bị CP6 — Demo 3 phút

Topic A, Nguyễn Văn Tứ, MSSV 2A202602586. Đây là tài liệu chuẩn bị; phần tập nói và trình bày trước giảng viên do học viên thực hiện.

Repo hiện được hoàn thiện và commit tại máy; không push theo yêu cầu của chủ repo. Học viên tự quyết định thời điểm đưa bài lên remote và nộp LMS.

## Mở sẵn trước khi được gọi

1. [REPORT.md](REPORT.md): claim, bảng 5 mức yaw và định nghĩa mẫu số.
2. [Biểu đồ yaw](../results/figures/yaw_sweep.png): displacement tăng, FOV gần như không đổi.
3. [Ảnh failure](../results/figures/fail_01_yaw_3deg_000004_object_1.png): cùng 26 điểm ở hai calibration.
4. Terminal ở thư mục gốc, dùng `.\.venv\Scripts\python.exe -m src.validate_projection` để demo kiểm tra nhanh khi cần.

## Nội dung nói theo thời gian

**0:00–0:25 — Câu hỏi và claim**

“Bài của em kiểm tra độ nhạy của phép chiếu LiDAR lên camera khi calibration lệch yaw. Claim là: trên ba frame KITTI 000019, 000011 và 000004, yaw lệch một độ làm trung vị độ dịch chuyển lớn hơn 10 pixel so với calibration gốc.”

**0:25–1:00 — Thí nghiệm có kiểm soát**

“Em dùng synthetic để kiểm tra phép chiếu và KITTI cho benchmark. Chuỗi biến đổi là P2, R0_rect và Tr_velo_to_cam; phải chia toạ độ đồng nhất và lọc điểm sau camera. Benchmark có năm mức yaw: 0; 0,5; 1; 2 và 3 độ. Ảnh, point cloud và các tham số khác giữ nguyên. Tập điểm tham chiếu được chọn ở baseline, rồi giữ cùng ID kể cả khi điểm lệch ra ngoài ảnh.”

**1:00–1:40 — Bằng chứng**

“Ở một độ, trung vị lần lượt là 14,728; 14,601 và 14,778 pixel, đều vượt 10 pixel. Ở ba độ, nó tăng lên khoảng 44 pixel. Có 15 dòng kết quả theo frame và 60 dòng theo object. Chương trình không lấy mẫu ngẫu nhiên; chạy lại cho CSV có cùng SHA256 trong cùng môi trường. Vì vậy claim được hỗ trợ trên ba frame này. Đây là so sánh với calibration gốc, không phải độ chính xác so với nhãn pixel độc lập.”

**1:40–2:30 — Failure và nguyên nhân**

“Ảnh này là một xe ở độ sâu 51,17 mét, có 26 điểm trong box 3D. Ở baseline, cả 26 điểm nằm trong box 2D. Khi yaw lệch ba độ, không điểm nào còn nằm trong box. Nguyên nhân thuộc lớp Geometry: extrinsic sai làm điểm dịch ngang. Nhưng FOV toàn frame chỉ giảm 0,0845 điểm phần trăm. Quy tắc báo động khi FOV giảm hơn một điểm phần trăm sẽ bỏ sót lỗi này. Đó là failure thuộc lớp Metric. Box xe xa nhỏ nên cùng độ dịch pixel làm giảm tỉ lệ điểm trong box mạnh.”

**2:30–3:00 — Khuyến nghị và giới hạn**

“Trong QA cho ADAS, nên kết hợp FOV với alignment theo object và range, đồng thời ghi timestamp, invalid ratio và số điểm mỗi object. GT box chỉ có ở đánh giá offline; chạy thật cần score từ edge hoặc box camera độc lập. Bước tiếp theo là thử nhiều frame, yaw âm, pitch và translation, hiệu chỉnh ngưỡng cảnh báo và đo latency. Bài hiện chưa kết luận thời gian thực hay độ chính xác của detector.”

## Câu hỏi có thể gặp

| Câu hỏi | Cách trả lời |
|---|---|
| Tại sao claim có thể bị bác bỏ? | Nếu một trong ba frame có median ở +1° không lớn hơn 10 px thì claim ban đầu sai. Số đo thực tế đều vượt ngưỡng. |
| LiDAR và camera dùng trục nào? | KITTI LiDAR: x trước, y trái, z lên; camera: x phải, y xuống, z trước. R0_rect phải nằm trong chuỗi biến đổi. |
| Vì sao cần P2 cột thứ tư? | Nó chứa phần tịnh tiến trong phép chiếu camera; chỉ lấy ma trận 3×3 sẽ bỏ mất thành phần này. Test đã kiểm tra bằng camera điểm biết trước. |
| Vì sao mask cần đúng ID điểm? | Nếu lọc riêng FOV ở mỗi lần rồi so hai mảng UV theo vị trí, chúng có thể thuộc những điểm khác nhau. Benchmark dùng mảng N hàng và một reference mask cố định. |
| Điểm mất khả năng chiếu thì sao? | Báo `n_unprojectable_reference` và `n_paired_points`; không gán sai lệch bằng 0. Cả 15 cấu hình hiện đều không có điểm reference mất khả năng chiếu. |
| Điểm trong box 3D được xác định thế nào? | Đưa điểm về hệ local của box bằng inverse yaw ở camera frame; x/z nằm trong nửa length/width, y nằm từ -height đến 0 vì location là tâm đáy. Giữ membership baseline qua sweep. |
| Vì sao baseline 000011 chỉ có 19,145% điểm object trong box? | Số tổng hợp bị Car gần có truncation 0,98 và 3.251 điểm chi phối. Mẫu số gồm cả điểm ngoài ảnh; xem CSV từng object, không quy ngay thành lỗi calibration. |
| Có phải lệch pixel tăng tuyến tính theo khoảng cách? | Với góc nhỏ, dịch pixel xấp xỉ theo tiêu cự × góc, không tăng trực tiếp theo range. Box vật xa nhỏ hơn nên cùng dịch pixel có thể làm alignment mất nhiều hơn. |
| FOV vì sao gần như không đổi? | Khi xoay nhẹ, điểm ra khỏi một biên có thể được thay bằng điểm đi vào từ biên khác; FOV chỉ đo tổng số điểm trong ảnh, không đo khớp vật thể. |
| 10 px và ngưỡng FOV 1 điểm phần trăm có dùng vận hành được chưa? | 10 px là ngưỡng claim của thí nghiệm; FOV 1 điểm phần trăm là quy tắc minh hoạ bị fail. Cần tập validation và đo miss/false alarm trước khi chọn ngưỡng triển khai. |
| Đổi sang nuScenes thì sao? | Chưa chạy cùng benchmark trên nuScenes. Trục LiDAR, tiêu cự ảnh, mật độ điểm và lệch thời gian khác; loader bù ego-motion. Chỉ đã kiểm tra overlay `scene-0103_010`, chưa mở rộng claim. |
| Có dùng AI không? | Có: Codex hỗ trợ code, thí nghiệm và báo cáo. Mục 6 REPORT khai báo đầy đủ; học viên cần tự chạy lại và giải thích các dòng code/số liệu. |

## Việc học viên cần thực hiện

- [ ] Chạy `.\.venv\Scripts\python.exe -m src.run_lab` và đọc các dòng PASS.
- [ ] Đọc `src/projection_metrics.py` và `src/benchmark_projection.py`, giải thích được mẫu số của từng metric.
- [ ] Tập nói với đồng hồ, gọn trong 3 phút; mở ảnh/REPORT trong vòng 30 giây khi được gọi.
- [ ] Trình bày và trả lời câu hỏi nếu được giảng viên gọi. Nếu không được gọi, REPORT là bằng chứng chấm phần trình bày.
- [ ] Nộp link repo và commit hash cuối cùng lên LMS Day 6 Lab; lấy hash bằng `git rev-parse HEAD`. Deadline theo `SUBMISSION.md`: 23:59 ngày 07/10/2026, UTC+7.
