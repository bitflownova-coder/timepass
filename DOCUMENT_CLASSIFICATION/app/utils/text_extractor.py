"""
Text Extraction Module - Extract text from PDFs and other document formats
"""
import PyPDF2
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class TextExtractor:
    """Extract text from various document formats"""
    
    @staticmethod
    def extract_from_pdf(file_path):
        """
        Extract text from PDF file
        
        Args:
            file_path (str): Path to PDF file
        
        Returns:
            tuple: (extracted_text: str, num_pages: int)
        """
        try:
            text = ""
            num_pages = 0
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            return text.strip(), num_pages
        
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return "", 0
    
    @staticmethod
    def extract_from_docx(file_path):
        """
        Extract text from DOCX file
        
        Args:
            file_path (str): Path to DOCX file
        
        Returns:
            str: Extracted text
        """
        try:
            from docx import Document
            
            doc = Document(file_path)
            text = ""
            
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text.strip()
        
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {str(e)}")
            return ""
    
    @staticmethod
    def extract_from_text_file(file_path, encoding='utf-8'):
        """
        Extract text from plain text file
        
        Args:
            file_path (str): Path to text file
            encoding (str): File encoding
        
        Returns:
            str: Extracted text
        """
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                text = file.read()
            return text.strip()
        
        except Exception as e:
            logger.error(f"Error extracting text from text file: {str(e)}")
            return ""
    
    @staticmethod
    def extract_text(file_path):
        """
        Extract text from any supported file format
        
        Args:
            file_path (str): Path to file
        
        Returns:
            dict: {
                'text': str,
                'num_pages': int or None,
                'success': bool,
                'file_type': str
            }
        """
        file_path = Path(file_path)
        file_extension = file_path.suffix.lower()
        
        result = {
            'text': '',
            'num_pages': None,
            'success': False,
            'file_type': file_extension
        }
        
        try:
            if file_extension == '.pdf':
                text, num_pages = TextExtractor.extract_from_pdf(file_path)
                result['text'] = text
                result['num_pages'] = num_pages
                result['success'] = bool(text)
            
            elif file_extension in ['.docx', '.doc']:
                text = TextExtractor.extract_from_docx(file_path)
                result['text'] = text
                result['success'] = bool(text)
            
            elif file_extension in ['.txt', '.text']:
                text = TextExtractor.extract_from_text_file(file_path)
                result['text'] = text
                result['success'] = bool(text)

            elif file_extension in ['.jpg', '.jpeg', '.png', '.bmp',
                                     '.tiff', '.tif', '.gif', '.webp']:
                from app.utils.ocr_processor import OCRProcessor
                ocr_result = OCRProcessor.extract_from_image(str(file_path))
                result['text'] = ocr_result.get('text', '')
                result['success'] = ocr_result.get('success', False)
                result['ocr_used'] = True
                result['ocr_confidence'] = ocr_result.get('confidence', 0.0)

            else:
                logger.warning(f"Unsupported file type: {file_extension}")
                result['success'] = False
        
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            result['success'] = False
        
        return result


class TextPreprocessor:
    """Preprocess extracted text for ML"""
    
    @staticmethod
    def clean_text(text):
        """
        Clean and normalize text
        
        Args:
            text (str): Raw text
        
        Returns:
            str: Cleaned text
        """
        import re
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    @staticmethod
    def tokenize(text):
        """
        Tokenize text into words
        
        Args:
            text (str): Text to tokenize
        
        Returns:
            list: List of tokens
        """
        return text.split()
    
    @staticmethod
    def remove_stopwords(tokens, stopwords_set=None):
        """
        Remove common stopwords
        
        Args:
            tokens (list): List of tokens
            stopwords_set (set): Set of stopwords to remove
        
        Returns:
            list: Filtered tokens
        """
        if stopwords_set is None:
            # English stopwords
            stopwords_set = {
                'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
                'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'or', 'that',
                'the', 'to', 'was', 'will', 'with', 'i', 'me', 'my', 'we', 'you',
                'your', 'this', 'these', 'those', 'what', 'which', 'who', 'why'
            }
        
        return [token for token in tokens if token not in stopwords_set]
    
    @staticmethod
    def preprocess(text):
        """
        Complete preprocessing pipeline
        
        Args:
            text (str): Raw text
        
        Returns:
            str: Preprocessed text
        """
        # Clean
        text = TextPreprocessor.clean_text(text)
        
        # Tokenize
        tokens = TextPreprocessor.tokenize(text)
        
        # Remove stopwords
        tokens = TextPreprocessor.remove_stopwords(tokens)
        
        # Rejoin
        return ' '.join(tokens)
