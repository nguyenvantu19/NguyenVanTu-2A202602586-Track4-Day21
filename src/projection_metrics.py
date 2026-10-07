"""Point correspondence and KITTI object geometry for the lab benchmark.

Original lab implementation, using the instructor's IO/projection helpers.
Unclipped projections preserve point IDs when perturbation moves them off image.
"""
import numpy as np

from starter.projection import velo_to_cam

CLASSES = ("Car", "Van", "Truck", "Pedestrian")


def project_all(points, calib, image_shape, min_depth=0.1):
    """Return uv (N,2), projectable (N,), in_image (N,), camera XYZ.

Invalid projections are NaN. Projectable requires finite XYZ, camera depth
above min_depth and a positive homogeneous denominator. FOV is separate.
"""
    cam = velo_to_cam(points[:, :3], calib)
    homogeneous = np.column_stack((cam, np.ones(len(cam))))
    with np.errstate(invalid="ignore", over="ignore"):
        q = homogeneous @ calib.P2.T
    valid = (np.isfinite(cam).all(axis=1) & (cam[:, 2] > min_depth)
             & np.isfinite(q).all(axis=1) & (q[:, 2] > 0))
    uv = np.full((len(points), 2), np.nan)
    with np.errstate(invalid="ignore", over="ignore", divide="ignore"):
        uv[valid] = q[valid, :2] / q[valid, 2:3]
    valid &= np.isfinite(uv).all(axis=1)
    height, width = image_shape[:2]
    inside = (valid & (uv[:, 0] >= 0) & (uv[:, 0] < width)
              & (uv[:, 1] >= 0) & (uv[:, 1] < height))
    return uv, valid, inside, cam


def points_in_object(cam, obj):
    """Fixed point membership in baseline 3D GT box (bottom-center KITTI).

KITTI camera Y points down: local Y is between -height and zero.
For row vectors, multiplying by R undoes the box's rotation R @ local.
"""
    h, w, length = obj.dimensions
    if min(h, w, length) <= 0:
        return np.zeros(len(cam), dtype=bool)
    c, s = np.cos(obj.rotation_y), np.sin(obj.rotation_y)
    rotation = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    local = (cam - obj.location) @ rotation
    return (np.isfinite(local).all(axis=1)
            & (np.abs(local[:, 0]) <= length / 2)
            & (np.abs(local[:, 2]) <= w / 2)
            & (local[:, 1] >= -h) & (local[:, 1] <= 0))


def inside_bbox(uv, bbox):
    x1, y1, x2, y2 = bbox
    return (np.isfinite(uv).all(axis=1)
            & (uv[:, 0] >= x1) & (uv[:, 0] <= x2)
            & (uv[:, 1] >= y1) & (uv[:, 1] <= y2))


def percent(numerator, denominator):
    return 100. * numerator / denominator if denominator else float("nan")
