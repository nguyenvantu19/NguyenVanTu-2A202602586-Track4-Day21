"""Deterministic yaw sweep with fixed point IDs and baseline 3D GT membership.

Run from repository root: python -m src.benchmark_projection --help.
No random sampling, model inference, downloaded code or fabricated metrics.
"""
import argparse
import csv
import json
import platform
from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from starter.datasets import list_frames, load_frame
from starter.projection import cam_to_image, perturb_extrinsic
from src.projection_metrics import CLASSES, inside_bbox, percent, points_in_object, project_all


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def benchmark_frame(data_root, frame_id, yaws, range_min, range_max, classes):
    fr = load_frame(data_root, frame_id)
    raw = fr["points"]
    points = raw[np.isfinite(raw).all(axis=1)]
    if not len(points):
        raise ValueError(f"Frame {frame_id} has no finite points")
    uv0, valid0, inside0, cam0 = project_all(points, fr["calib"], fr["image"].shape)
    ranges = np.linalg.norm(points[:, :3], axis=1)
    reference = inside0 & (ranges >= range_min) & (ranges <= range_max)
    if not reference.any():
        raise ValueError(f"Frame {frame_id} has no baseline reference points")
    objects = [(idx, obj, points_in_object(cam0, obj))
               for idx, obj in enumerate(fr["labels"]) if obj.type in classes]
    frame_rows, object_rows = [], []
    for yaw in yaws:
        calib = perturb_extrinsic(fr["calib"], yaw_deg=yaw)
        uv, valid, inside, cam = project_all(points, calib, fr["image"].shape)
        # Ensure unclipped metric projection and the public overlay API agree.
        clipped_uv, _, clipped_mask = cam_to_image(cam, calib.P2, fr["image"].shape)
        np.testing.assert_array_equal(inside, clipped_mask)
        np.testing.assert_allclose(uv[inside], clipped_uv, atol=1e-10, rtol=1e-10)
        paired = reference & valid
        displacement = np.linalg.norm(uv[paired] - uv0[paired], axis=1)
        n_object_points = n_object_inside = 0
        for idx, obj, membership in objects:
            n = int(membership.sum())
            n_inside = int((membership & inside & inside_bbox(uv, obj.bbox)).sum())
            n_object_points += n
            n_object_inside += n_inside
            object_rows.append({
                "frame_id": frame_id, "yaw_deg": yaw, "object_id": idx,
                "class": obj.type, "depth_m": float(obj.location[2]),
                "occluded": obj.occluded, "truncated": obj.truncated,
                "n_object_points": n, "n_inside_2d_box": n_inside,
                "inside_2d_box_pct": percent(n_inside, n),
            })
        frame_rows.append({
            "frame_id": frame_id, "yaw_deg": yaw,
            "n_raw_points": len(raw), "n_finite_points": len(points),
            "n_reference_points": int(reference.sum()),
            "n_paired_points": int(paired.sum()),
            "n_unprojectable_reference": int((reference & ~valid).sum()),
            "median_displacement_px": float(np.median(displacement)) if len(displacement) else float("nan"),
            "p95_displacement_px": float(np.percentile(displacement, 95)) if len(displacement) else float("nan"),
            "n_inside_fov": int(inside.sum()), "inside_fov_pct": percent(int(inside.sum()), len(points)),
            "n_object_points": n_object_points, "n_object_inside_2d_box": n_object_inside,
            "object_inside_2d_box_pct": percent(n_object_inside, n_object_points),
            "range_min_m": range_min, "range_max_m": range_max,
        })
    return frame_rows, object_rows


def plot_rows(rows, output):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.4), layout="constrained")
    specs = [("median_displacement_px", "Fixed-point median shift", "Displacement (pixels)"),
             ("inside_fov_pct", "Global camera field of view", "Finite points inside image (%)"),
             ("object_inside_2d_box_pct", "GT object alignment", "Object points inside their 2D box (%)")]
    for frame in dict.fromkeys(row["frame_id"] for row in rows):
        subset = [row for row in rows if row["frame_id"] == frame]
        for ax, (key, title, ylabel) in zip(axes, specs):
            ax.plot([r["yaw_deg"] for r in subset], [r[key] for r in subset], marker="o", label=frame)
            ax.set(xlabel="LiDAR yaw drift (degrees)", ylabel=ylabel, title=title)
            ax.grid(alpha=0.2)
    axes[0].axhline(10, color="#b45309", linestyle="--", linewidth=1, label="Claim: >10 px at 1 deg")
    axes[0].legend(fontsize=8)
    axes[1].legend(fontsize=8)
    axes[2].set_ylim(0, 105)
    fig.suptitle("LiDAR-camera calibration sensitivity | same input points, yaw only", fontsize=13)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", default="data/kitti_mini")
    parser.add_argument("--frames", nargs="+", default=["000019", "000011", "000004"])
    parser.add_argument("--yaws", type=float, nargs="+", default=[0., 0.5, 1., 2., 3.])
    parser.add_argument("--range-min", type=float, default=3.)
    parser.add_argument("--range-max", type=float, default=80.)
    parser.add_argument("--classes", nargs="+", default=list(CLASSES))
    parser.add_argument("--out-dir", type=Path, default=Path("results"))
    args = parser.parse_args()
    if (not 0 <= args.range_min < args.range_max or len(set(args.yaws)) < 3
            or not np.isfinite(args.yaws).all() or len(set(args.frames)) != len(args.frames)):
        parser.error("Use finite yaw values (>=3 unique levels), unique frames and valid range limits")
    available = set(list_frames(args.data_root))
    if set(args.frames) - available:
        parser.error(f"Unknown frames: {sorted(set(args.frames) - available)}")
    rows, object_rows = [], []
    for frame in args.frames:
        frame_rows, objs = benchmark_frame(args.data_root, frame, args.yaws,
                                          args.range_min, args.range_max, args.classes)
        rows.extend(frame_rows)
        object_rows.extend(objs)
    write_csv(args.out_dir / "yaw_perturb_sweep.csv", rows)
    if object_rows:
        write_csv(args.out_dir / "yaw_object_sweep.csv", object_rows)
    plot_rows(rows, args.out_dir / "figures" / "yaw_sweep.png")
    config = {"data_root": Path(args.data_root).as_posix(), "frames": args.frames,
              "yaw_degrees": args.yaws, "range_xyz_m": [args.range_min, args.range_max],
              "classes": args.classes, "min_depth_m": 0.1, "pitch_roll_translation": 0,
              "random_sampling": False, "seed": None,
              "primary_reference": "finite XYZI, baseline image FOV, XYZ range; fixed IDs",
              "fov_denominator": "all finite XYZI points, without range filter",
              "object_denominator": "sum of baseline 3D GT memberships, including off-image points",
              "python": platform.python_version(), "numpy": np.__version__,
              "opencv": cv2.__version__, "matplotlib": matplotlib.__version__}
    (args.out_dir / "experiment_config.json").write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for row in rows:
        print(f"{row['frame_id']} yaw={row['yaw_deg']:g}: median={row['median_displacement_px']:.3f}px "
              f"FOV={row['inside_fov_pct']:.3f}% object={row['object_inside_2d_box_pct']:.3f}% "
              f"unprojectable={row['n_unprojectable_reference']}")
    print(f"Saved {len(rows)} frame rows and {len(object_rows)} object rows to {args.out_dir}")


if __name__ == "__main__":
    main()
