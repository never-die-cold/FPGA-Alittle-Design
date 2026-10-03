"""定位黄金参考：亮背景上的暗目标，4 连通；不输出分类或工单通过结论。"""
from collections import deque


def locate(image, frame_id, config_id, threshold=96, min_area=8, max_targets=16):
    h = len(image)
    w = len(image[0]) if h else 0
    if not w or any(len(row) != w for row in image):
        raise ValueError("nonempty rectangular image required")
    if not 0 <= threshold <= 255 or min_area < 1 or max_targets < 1:
        raise ValueError("invalid segmentation parameters")
    if any(not isinstance(p, int) or not 0 <= p <= 255 for row in image for p in row):
        raise ValueError("pixels must be unsigned 8-bit integers")
    seen = bytearray(w * h)
    targets = []
    for y in range(h):
        for x in range(w):
            if seen[y*w+x] or image[y][x] >= threshold:
                continue
            queue = deque([(x, y)])
            seen[y*w+x] = 1
            x0 = x1 = x
            y0 = y1 = y
            area = 0
            while queue:
                px, py = queue.popleft()
                area += 1
                x0, x1 = min(x0, px), max(x1, px)
                y0, y1 = min(y0, py), max(y1, py)
                for nx, ny in ((px-1, py), (px+1, py), (px, py-1), (px, py+1)):
                    if 0 <= nx < w and 0 <= ny < h:
                        i = ny*w+nx
                        if not seen[i] and image[ny][nx] < threshold:
                            seen[i] = 1
                            queue.append((nx, ny))
            if area >= min_area:
                targets.append({"target_id": len(targets), "frame_id": frame_id,
                                "config_id": config_id, "bbox": [x0, y0, x1, y1],
                                "area": area, "touches_border": x0 == 0 or y0 == 0 or x1 == w-1 or y1 == h-1})
    status = "LOCATION_ONLY"
    if len(targets) > max_targets:
        status = "RECHECK_TARGET_LIMIT"
    elif any(t["touches_border"] for t in targets):
        status = "RECHECK_BORDER"
    return {"frame_id": frame_id, "config_id": config_id, "width": w, "height": h,
            "status": status, "targets": targets}


def crop_resize(image, bbox, width, height):
    """闭区间 bbox → 中心对齐 16.16 双线性；与 scaler 两级 8-bit lerp 口径相同。"""
    x0, y0, x1, y1 = bbox
    if width < 1 or height < 1 or not (0 <= x0 <= x1 < len(image[0]) and 0 <= y0 <= y1 < len(image)):
        raise ValueError("invalid crop or output size")
    sw, sh = x1-x0+1, y1-y0+1
    def coord(d, source, dest):
        # Verilog 有符号除法向零截断，不使用浮点。
        n = (source-dest) * 32768
        start = (abs(n) // dest) * (1 if n >= 0 else -1)
        a = max(0, min((source-1)*65536, start + d*(source*65536//dest)))
        i = a >> 16
        return i, min(i+1, source-1), (a >> 8) & 255
    result = []
    for y in range(height):
        ay, by, fy = coord(y, sh, height)
        row = []
        for x in range(width):
            ax, bx, fx = coord(x, sw, width)
            top = ((256-fx)*image[y0+ay][x0+ax] + fx*image[y0+ay][x0+bx]) >> 8
            bot = ((256-fx)*image[y0+by][x0+ax] + fx*image[y0+by][x0+bx]) >> 8
            row.append(((256-fy)*top + fy*bot) >> 8)
        result.append(row)
    return result


def prepare_targets(image, result, width, height):
    if result["status"] != "LOCATION_ONLY":
        raise ValueError("recheck required before inference")
    return [{**t, "pixels": crop_resize(image, t["bbox"], width, height),
             "pixel_format": "GRAY8", "input_size": [width, height]} for t in result["targets"]]
