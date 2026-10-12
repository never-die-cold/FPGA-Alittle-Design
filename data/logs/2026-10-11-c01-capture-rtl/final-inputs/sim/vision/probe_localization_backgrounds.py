"""Deterministic synthetic counterexamples, not real-camera accuracy estimates."""
import argparse
import json
from pathlib import Path
import cv2
import numpy as np
from localization_opencv import detect_boxes, score_boxes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    cv2.setNumThreads(1)
    y, x = np.mgrid[:720, :1280]
    cases = {
        'empty_uniform': np.full((720,1280), 40, np.uint8),
        'empty_gradient': np.tile(np.linspace(20,120,1280).astype(np.uint8), (720,1)),
        'empty_center_light': (30+70*np.exp(-((x-640)**2+(y-360)**2)/100000)).astype(np.uint8),
    }
    records = []
    for name, background in cases.items():
        for with_object in [False, True]:
            image = cv2.cvtColor(background, cv2.COLOR_GRAY2BGR)
            truth = [(550,290,730,430)] if with_object else []
            if with_object:
                image[290:430,550:730] = 230
            boxes = detect_boxes(image)
            result = {'case': name, 'object_present': with_object, 'boxes': boxes,
                      **score_boxes(boxes, truth)}
            records.append(result)
            for x0,y0,x1,y1 in boxes:
                cv2.rectangle(image, (x0,y0), (x1-1,y1-1), (0,0,255), 2)
            cv2.imwrite(str(args.output / f'{name}-{int(with_object)}.png'), image)
    (args.output / 'report.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
    print(json.dumps(records), flush=True)


if __name__ == '__main__':
    main()
