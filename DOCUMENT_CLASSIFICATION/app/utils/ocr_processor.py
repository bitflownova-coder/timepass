"""
OCR Processor - Extract text from images using Tesseract OCR
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import pytesseract
    from PIL import Image, ImageFilter, ImageOps
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("pytesseract/Pillow not installed — OCR disabled")

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif', '.webp'}


class OCRProcessor:
    """Extract text from images using Tesseract OCR."""

    @staticmethod
    def is_available() -> bool:
        return TESSERACT_AVAILABLE

    @staticmethod
    def is_image(filename: str) -> bool:
        return Path(filename).suffix.lower() in IMAGE_EXTENSIONS

    @staticmethod
    def extract_from_image(image_path: str) -> dict:
        """
        Extract text from an image file.

        Returns:
            dict: {success, text, confidence, word_count, method}
        """
        if not TESSERACT_AVAILABLE:
            return {'success': False,
                    'error': 'OCR unavailable (pytesseract not installed)',
                    'text': ''}
        try:
            path = Path(image_path)
            if not path.exists():
                return {'success': False, 'error': 'File not found', 'text': ''}

            img = Image.open(str(path))

            # Normalise colour mode
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')

            # Upscale small images for better recognition
            w, h = img.size
            if w < 1000:
                scale = 1000 / w
                img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

            # Convert to grayscale + sharpen
            img = img.convert('L')
            img = img.filter(ImageFilter.SHARPEN)

            data = pytesseract.image_to_data(img,
                                              output_type=pytesseract.Output.DICT)
            words, confs = [], []
            for i, conf in enumerate(data['conf']):
                try:
                    c = int(conf)
                    if c > 30:
                        w_text = data['text'][i].strip()
                        if w_text:
                            words.append(w_text)
                            confs.append(c)
                except (ValueError, TypeError):
                    continue

            text = ' '.join(words)
            avg_conf = sum(confs) / len(confs) / 100.0 if confs else 0.0

            return {
                'success': bool(text),
                'text': text,
                'confidence': round(avg_conf, 4),
                'word_count': len(words),
                'method': 'tesseract',
            }
        except Exception as e:
            logger.error(f"OCR error for {image_path}: {e}")
            return {'success': False, 'error': str(e), 'text': ''}
