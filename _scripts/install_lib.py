# -*- coding: utf-8 -*-
"""
install_lib.py — однократное восстановление библиотек конвертера в _scripts/lib.
Запуск (локально, на любом ПК):
    python _scripts/install_lib.py

Что устанавливает (рендер PDF + русский OCR), без pip:
    PyMuPDF, rapidocr-onnxruntime, onnxruntime, opencv-python-headless,
    numpy, pyclipper, shapely, PyYAML, six, tqdm, packaging, pyparsing

Схема: скачивает wheel'ы (zip) с PyPI напрямую и распаковывает в _scripts/lib.
Папка _scripts/lib/* исключена из Git (.gitignore) — здесь её можно воссоздать.
"""
import os, sys, urllib.request, json, zipfile

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_pipsrc')
os.makedirs(LIB, exist_ok=True)
os.makedirs(CACHE, exist_ok=True)


def get(url):
    with urllib.request.urlopen(
        urllib.request.Request(url, headers={'User-Agent': 'dsh'}), timeout=30
    ) as r:
        return json.load(r)


def dl(url, fname):
    dest = os.path.join(CACHE, fname)
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        print("  cached:", fname)
        return dest
    req = urllib.request.Request(url, headers={'User-Agent': 'dsh'})
    with urllib.request.urlopen(req, timeout=180) as r, open(dest, 'wb') as f:
        f.write(r.read())
    print("  downloaded:", fname, os.path.getsize(dest) // (1024*1024), "MB")
    return dest


def unpack(whl):
    with zipfile.ZipFile(whl) as z:
        z.extractall(LIB)
    print("  unpacked:", os.path.basename(whl))


def pick_cp314_nont(pkg):
    """choose the plain cp314 win_amd64 wheel (NOT the cp314t free-threaded build)."""
    j = get('https://pypi.org/pypi/%s/json' % pkg)
    for u in j["urls"]:
        f = u["filename"]
        if ('cp314-cp314-win_amd64' in f and f.endswith('.whl')
                and 'cp314t' not in f):
            return u
        if pkg == 'pyclipper' or pkg == 'shapely':
            # fallback to platform wheel for cp314 if plain exists
            pass
    # fallback: any win_amd64 cp314
    for u in j["urls"]:
        f = u["filename"]
        if 'win_amd64' in f and 'cp314' in f and f.endswith('.whl') and 'cp314t' not in f:
            return u
    # last resort: any win_amd64
    for u in j["urls"]:
        if 'win_amd64' in u["filename"] and u["filename"].endswith('.whl'):
            return u
    return None


def pick_pure(pkg):
    j = get('https://pypi.org/pypi/%s/json' % pkg)
    for u in j["urls"]:
        if 'none-any' in u["filename"] and u["filename"].endswith('.whl'):
            return u
    return None


def pick_onnx():
    j = get('https://pypi.org/pypi/onnxruntime/json')
    for u in j["urls"]:
        f = u["filename"]
        if 'cp314' in f and 'win_amd64' in f and f.endswith('.whl'):
            return u
    return None


def pick_openv():
    j = get('https://pypi.org/pypi/opencv-python-headless/json')
    for u in j["urls"]:
        f = u["filename"]
        if 'abi3' in f and 'win_amd64' in f and f.endswith('.whl'):
            return u
    return None


def pick_rapid():
    j = get('https://pypi.org/pypi/rapidocr-onnxruntime/json')
    for u in j["urls"]:
        if 'none-any' in u["filename"] and u["filename"].endswith('.whl'):
            return u
    return None


def main():
    print("Installing PDF/OCR libraries into:", LIB)

    pkg_and_picker = [
        ('rapidocr-onnxruntime', pick_rapid),
        ('onnxruntime', pick_onnx),
        ('opencv-python-headless', pick_openv),
        ('numpy', pick_cp314_nont),
        ('pyclipper', pick_cp314_nont),
        ('shapely', pick_cp314_nont),
        ('PyYAML', pick_cp314_nont),
    ]
    for pkg, picker in pkg_and_picker:
        u = picker(pkg)
        if not u:
            print("  !! no wheel for", pkg)
            continue
        whl = dl(u["url"], u["filename"])
        unpack(whl)

    for pkg in ['six', 'tqdm', 'packaging', 'pyparsing']:
        u = pick_pure(pkg)
        if u:
            whl = dl(u["url"], u["filename"])
            unpack(whl)

    print("\nDone. Verify with:")
    print("  python -c \"import sys; sys.path.insert(0, r'%s'); " % LIB
          + "import pymupdf, onnxruntime, cv2, numpy; from rapidocr_onnxruntime import RapidOCR; print('OK')\"")


if __name__ == '__main__':
    main()
