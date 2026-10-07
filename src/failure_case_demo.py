"""Show the same GT-object LiDAR points before/after deliberate yaw drift.

Default case: KITTI 000004, far Car at 51.17 m, yaw +3 degrees.
The second failure is a deliberately simple global-FOV alarm missing this drift.
Run from the repository root: python -m src.failure_case_demo --help.
"""
import argparse
from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

from starter.datasets import load_frame
from starter.projection import perturb_extrinsic
from src.benchmark_projection import write_csv
from src.projection_metrics import inside_bbox, percent, points_in_object, project_all


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", default="data/kitti_mini")
    parser.add_argument("--frame", default="000004")
    parser.add_argument("--object-id", type=int, default=1, help="0-based row index in parsed GT labels")
    parser.add_argument("--yaw", type=float, default=3.)
    parser.add_argument("--fov-alarm-drop-pp", type=float, default=1., help="Illustrative threshold, not calibrated")
    parser.add_argument("--out-dir", type=Path, default=Path("results"))
    args = parser.parse_args()
    if not np.isfinite(args.yaw) or not np.isfinite(args.fov_alarm_drop_pp) or args.fov_alarm_drop_pp < 0:
        parser.error("yaw must be finite and FOV alarm threshold nonnegative/finite")
    fr = load_frame(args.data_root, args.frame)
    if not 0 <= args.object_id < len(fr["labels"]):
        parser.error("object-id outside label list")
    obj = fr["labels"][args.object_id]
    points = fr["points"][np.isfinite(fr["points"]).all(axis=1)]
    uv0, valid0, inside0, cam0 = project_all(points, fr["calib"], fr["image"].shape)
    membership = points_in_object(cam0, obj)
    total = int(membership.sum())
    if not total:
        parser.error("selected object has no baseline 3D-box points")
    uv1, valid1, inside1, _ = project_all(
        points, perturb_extrinsic(fr["calib"], yaw_deg=args.yaw), fr["image"].shape)
    counts = [int((membership & inside & inside_bbox(uv, obj.bbox)).sum())
              for uv, inside in ((uv0, inside0), (uv1, inside1))]
    fovs = [percent(int(inside.sum()), len(points)) for inside in (inside0, inside1)]
    drop_pp = fovs[0] - fovs[1]
    alarm = drop_pp > args.fov_alarm_drop_pp
    rows = [{"frame_id": args.frame, "object_id": args.object_id, "class": obj.type,
             "depth_m": float(obj.location[2]), "yaw_deg": yaw,
             "n_object_points": total, "n_inside_2d_box": count,
             "inside_2d_box_pct": percent(count, total), "inside_fov_pct": fov,
             "fov_drop_from_baseline_pp": fovs[0] - fov,
             "fov_alarm_threshold_pp": args.fov_alarm_drop_pp,
             "fov_alarm": (fovs[0] - fov) > args.fov_alarm_drop_pp}
            for yaw, count, fov in zip((0., args.yaw), counts, fovs)]
    write_csv(args.out_dir / "failure_case.csv", rows)

    image = cv2.cvtColor(fr["image"], cv2.COLOR_BGR2RGB)
    x1, y1, x2, y2 = obj.bbox
    visible_points = np.vstack((uv0[membership & valid0], uv1[membership & valid1]))
    if not len(visible_points):
        parser.error("selected object has no projectable points")
    left = max(0, min(x1, visible_points[:, 0].min()) - 22)
    right = min(image.shape[1], max(x2, visible_points[:, 0].max()) + 22)
    top = max(0, min(y1, visible_points[:, 1].min()) - 28)
    bottom = min(image.shape[0], max(y2, visible_points[:, 1].max()) + 28)
    fig = plt.figure(figsize=(12, 7.3), layout="constrained")
    grid = fig.add_gridspec(2, 2, height_ratios=[1.15, 1.])
    overview = fig.add_subplot(grid[0, :])
    overview.imshow(image)
    overview.add_patch(Rectangle((left, top), right-left, bottom-top, fill=False,
                                edgecolor="#ffca28", linewidth=2))
    overview.annotate("Zoom: far car", xy=((x1+x2)/2, y1), xytext=(x2+100, y1-65),
                      color="#ffca28", fontsize=12,
                      arrowprops={"arrowstyle": "->", "color": "#ffca28", "lw": 2})
    overview.set_title(f"KITTI {args.frame} | {obj.type} #{args.object_id} | GT depth {obj.location[2]:.2f} m")
    overview.axis("off")
    for index, (uv, valid, yaw, color) in enumerate(
            ((uv0, valid0, 0., "#00e5ff"), (uv1, valid1, args.yaw, "#ff7043"))):
        ax = fig.add_subplot(grid[1, index])
        ax.imshow(image)
        ax.add_patch(Rectangle((x1, y1), x2-x1, y2-y1, fill=False,
                              edgecolor="#76ff03", linewidth=2, label="Fixed GT 2D box"))
        pts = uv[membership & valid]
        ax.scatter(pts[:, 0], pts[:, 1], s=24, color=color, edgecolors="black", linewidths=0.35,
                   label=f"Same {total} object points")
        ax.set_xlim(left, right)
        ax.set_ylim(bottom, top)
        ax.set_title(f"Yaw {yaw:+g} deg | in box {counts[index]}/{total} ({percent(counts[index], total):.1f}%)")
        ax.legend(loc="lower left", fontsize=8)
        ax.axis("off")
    fig.suptitle("Geometry failure: object points move outside their camera box", fontsize=15)
    fig.supxlabel(f"Global FOV {fovs[0]:.3f}% -> {fovs[1]:.3f}% | drop {drop_pp:.3f} percentage points\n"
                  f"Illustrative alarm: FOV drop > {args.fov_alarm_drop_pp:g} pp | alarm = {alarm} | "
                  "Image source: KITTI Vision Benchmark Suite", fontsize=10)
    out = args.out_dir / "figures" / f"fail_01_yaw_{args.yaw:g}deg_{args.frame}_object_{args.object_id}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=180)
    plt.close(fig)
    print(f"Object {args.object_id}: {counts[0]}/{total} -> {counts[1]}/{total}; "
          f"FOV drop={drop_pp:.6f} pp; illustrative alarm={alarm}")
    print(out)


if __name__ == "__main__":
    main()
