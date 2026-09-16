# -*- coding: utf-8 -*-
"""
pdf2md.py — конвертер отсканированного PDF в Markdown текст для Vault.
Использует PyMuPDF (рендер) + RapidOCR (русский OCR).
Каждый воркер-поток держит свой экземпляр RapidOCR (thread-local).

Запуск:
  python _scripts/pdf2md.py --pdf "raw/Афнфсьев.2012.PDF" \
      --start 132 --end 180 --out "01_Сырьё/Гистология/Глава_07.md" --workers 4
"""
import sys, os, time, argparse, io, threading
from concurrent.futures import ThreadPoolExecutor, as_completed

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')
sys.path.insert(0, LIB)
import numpy as np
import pymupdf
from rapidocr_onnxruntime import RapidOCR

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(LIB, 'rapidocr_onnxruntime', 'models')
REC_MODEL = os.path.join(MODELS, 'cyrillic_PP-OCRv3_rec_infer.onnx')
REC_KEYS = os.path.join(MODELS, 'cyrillic_dict.txt')

_tls = threading.local()


def get_ocr():
    if not hasattr(_tls, 'ocr'):
        _tls.ocr = RapidOCR(
            rec_model_path=REC_MODEL, rec_keys_path=REC_KEYS, print_verbose=False)
    return _tls.ocr


def ocr_image(ocr, pix):
    if pix.n == 4:
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 4)[:, :, :3]
    elif pix.n == 1:
        g = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
        img = np.repeat(g[:, :, None], 3, axis=2)
    else:
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    res, _ = ocr(img)
    return res


def group_lines(result):
    if not result:
        return []
    items = []
    for box, text, _score in result:
        xs = [pt[0] for pt in box]
        ys = [pt[1] for pt in box]
        items.append((min(ys), min(xs), max(ys), max(xs), text))
    items.sort(key=lambda t: (int(t[0] // 10), t[1]))
    lines = []
    cur = None
    for (y0, x0, y1, x1, text) in items:
        if cur is None or y0 > cur[3] + 5:
            if cur:
                lines.append(" ".join(cur[4]))
            cur = [y0, x0, y1, x1, [text]]
        else:
            cur[4].append(text)
            cur[1] = min(cur[1], x0)
            cur[3] = max(cur[3], y1)
            cur[2] = max(cur[2], y1)
    if cur:
        lines.append(" ".join(cur[4]))
    return [ln.strip() for ln in lines if ln.strip()]


def page_to_markdown(pdf_path, idx):
    doc = pymupdf.open(pdf_path)
    try:
        pix = doc[idx].get_pixmap(matrix=pymupdf.Matrix(2, 2))
    finally:
        doc.close()
    res = ocr_image(get_ocr(), pix)
    raw_lines = group_lines(res)
    # join into paragraphs
    paras = []
    buf = []
    for ln in raw_lines:
        if not ln:
            if buf:
                paras.append(" ".join(buf)); buf = []
        else:
            buf.append(ln)
    if buf:
        paras.append(" ".join(buf))
    if not paras:
        return ""  # blank page
    header = "\n\n<!-- PDF page %d -->\n\n" % (idx + 1)
    return header + "\n\n".join(paras)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pdf', required=True)
    ap.add_argument('--start', type=int, default=None)
    ap.add_argument('--end', type=int, default=None)
    ap.add_argument('--out', default=None)
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--page', type=int, default=None, help="single page only")
    args = ap.parse_args()

    doc = pymupdf.open(args.pdf)
    total = doc.page_count
    page_w = doc[0].rect.width
    page_h = doc[0].rect.height
    doc.close()

    if args.page is not None:
        pages = [args.page]
    else:
        s = args.start if args.start is not None else 0
        e = args.end if args.end is not None else total
        pages = list(range(s, min(e, total)))

    print("Processing %d pages with %d workers... (%d x %d pt)" %
          (len(pages), args.workers, page_w, page_h), flush=True)
    t0 = time.time()
    results = {}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(page_to_markdown, args.pdf, p): p for p in pages}
        done = 0
        for fut in as_completed(futs):
            p = futs[fut]
            try:
                results[p] = fut.result()
            except Exception as e:
                results[p] = "<!-- page %d ERROR: %s -->" % (p + 1, e)
            done += 1
            if done % 10 == 0:
                print("  %d/%d (%.0fs)" % (done, len(pages), time.time() - t0), flush=True)

    ordered = "\n".join(results[p] for p in pages)
    print("Done in %.1fs" % (time.time() - t0), flush=True)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with io.open(args.out, 'w', encoding='utf-8') as f:
            f.write(ordered)
        print("WROTE %s (%d chars)" % (args.out, len(ordered)), flush=True)
    else:
        sys.stdout.buffer.write(ordered.encode('utf-8')[:6000])


if __name__ == '__main__':
    main()
