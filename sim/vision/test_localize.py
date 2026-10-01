"""合成数据验证定位契约；真实反光/阴影/接触效果需要采样验收。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "data/golden/vision/localize"))
from reference import locate, crop_resize, prepare_targets


def main():
    image = [[240] * 32 for _ in range(24)]
    assert locate(image, 7, 3)["targets"] == []
    for y in range(3, 8):
        for x in range(2, 6):
            image[y][x] = 20
    for y in range(11, 16):
        for x in range(20, 27):
            image[y][x] = 30
    image[20][10] = 0  # 孤立噪点被面积过滤
    result = locate(image, 7, 3)
    assert [t["bbox"] for t in result["targets"]] == [[2, 3, 5, 7], [20, 11, 26, 15]]
    assert [t["area"] for t in result["targets"]] == [20, 35]
    assert all(t["frame_id"] == 7 and t["config_id"] == 3 for t in result["targets"])
    crops = prepare_targets(image, result, 8, 4)
    assert crops[0]["pixels"] == [[20]*8 for _ in range(4)]
    assert crops[1]["pixels"] == [[30]*8 for _ in range(4)]
    assert crops[1]["bbox"] == [20, 11, 26, 15] and crops[1]["input_size"] == [8, 4]
    assert crop_resize([[0, 64], [128, 255]], [0, 0, 1, 1], 1, 1) == [[111]]
    assert crop_resize([[173]], [0, 0, 0, 0], 3, 2) == [[173]*3]*2
    golden_root = Path(__file__).resolve().parents[2] / "data/golden/vision"
    for folder, sw, sh, dw, dh in (("scaler", 16, 8, 32, 16), ("scaler_ds", 32, 16, 8, 4)):
        source = [int(p, 16) for p in (golden_root/folder/"input_gray.hex").read_text().split()]
        expected = [int(p, 16) for p in (golden_root/folder/"expected_y.hex").read_text().split()]
        scaled = crop_resize([source[y*sw:(y+1)*sw] for y in range(sh)], [0, 0, sw-1, sh-1], dw, dh)
        assert [p for row in scaled for p in row] == expected
    try:
        prepare_targets(image, locate(image, 7, 3, max_targets=1), 8, 4)
        raise AssertionError("recheck scene accepted")
    except ValueError:
        pass
    assert locate(image, 7, 3, max_targets=1)["status"] == "RECHECK_TARGET_LIMIT"
    image[0][0:8] = [0] * 8
    assert locate(image, 8, 3)["status"] == "RECHECK_BORDER"
    try:
        locate([[0], [0, 1]], 1, 1)
        raise AssertionError("malformed image accepted")
    except ValueError:
        pass
    print("PASS: localization empty/multiple/non-grid/noise/limit/border + per-target crop/resize/frame metadata")


if __name__ == "__main__":
    main()
