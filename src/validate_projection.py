"""Independent geometry checks; run: python -m src.validate_projection.

Uses the instructor's synthetic calibration and analytically defined camera
points. No external source code or random inputs are used.
"""
import numpy as np

from starter.datasets import load_frame
from starter.projection import cam_to_image, velo_to_cam


def main():
    fr = load_frame("data/synthetic", "000000")
    cam = velo_to_cam(np.array([[10., 0., 0.]]), fr["calib"])
    uv, _, mask = cam_to_image(cam, fr["calib"].P2, fr["image"].shape)
    np.testing.assert_allclose(cam[0, 2], 9.73, atol=0.02)
    np.testing.assert_allclose(uv[0], [614., 175.], atol=2.)
    assert mask.tolist() == [True]
    print(f"PASS synthetic (10,0,0): z={cam[0, 2]:.5f}, uv={uv[0]}")

    # Analytic u=x/z, v=y/z. Width/height have exclusive upper bounds.
    P = np.column_stack((np.eye(3), np.zeros(3)))
    points = np.array([[2, 4, 2], [0, 0, 1], [10, 0, 1], [0, 10, 1],
                       [-1, 0, 1], [0, 0, -1], [0, 0, 0.1],
                       [np.nan, 0, 1], [0, np.inf, 1], [0, 0, 0]])
    uv, depth, mask = cam_to_image(points, P, (10, 10, 3))
    assert mask.tolist() == [True, True] + [False] * 8
    np.testing.assert_allclose(uv, [[1, 2], [0, 0]])
    np.testing.assert_allclose(depth, [2, 1])
    # P2's fourth column must participate in projection.
    shifted = P.copy()
    shifted[0, 3] = 2
    np.testing.assert_allclose(cam_to_image(points[:1], shifted, (10, 10))[0], [[2, 2]])
    # Guard zero homogeneous denominator even with positive camera depth.
    singular = P.copy()
    singular[2] = 0
    assert not cam_to_image(points[:1], singular, (10, 10))[2].any()
    for empty in (np.empty((0, 3)), points[7:9]):
        a, b, c = cam_to_image(empty, P, (10, 10))
        assert a.shape == (0, 2) and b.shape == (0,) and c.shape == (len(empty),)
    assert velo_to_cam(np.empty((0, 3)), fr["calib"]).shape == (0, 3)
    print("PASS depth/FOV boundaries, NaN/Inf, empty input, homogeneous translation and zero denominator")


if __name__ == "__main__":
    main()
