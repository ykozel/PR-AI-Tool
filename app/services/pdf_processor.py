"""PDF processing service for extracting text and metadata from PDF files"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

import PyPDF2
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Handles PDF extraction, OCR, and text parsing"""

    def __init__(self, temp_dir: str = "/tmp/pdf_processing"):
        """Initialize PDF processor with temporary directory"""
        self.temp_dir = temp_dir
        Path(temp_dir).mkdir(parents=True, exist_ok=True)

    def extract_text_from_pdf(self, file_path: str) -> Optional[str]:
        """
        Extract text from PDF using both text-based and OCR methods
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text or None if extraction fails
        """
        try:
            # First attempt: Extract text directly from PDF
            text = self._extract_text_direct(file_path)
            
            # If text extraction yields minimal results, try OCR
            if not text or len(text.strip()) < 100:
                logger.info(f"Direct text extraction minimal for {file_path}, attempting OCR")
                text = self._extract_text_ocr(file_path)
            
            return text if text else None
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            return None

    def _extract_text_direct(self, file_path: str) -> str:
        """Extract text directly from PDF using PyPDF2"""
        try:
            text = []
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                logger.info(f"PDF has {num_pages} pages")
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text.append(f"--- Page {page_num + 1} ---\n{page_text}")
            
            return "\n".join(text)
        except Exception as e:
            logger.warning(f"Direct text extraction failed: {str(e)}")
            return ""

    def _extract_text_ocr(self, file_path: str) -> str:
        """Extract text from PDF using OCR (pytesseract)"""
        try:
            # Convert PDF pages to images
            images = convert_from_path(file_path)
            text_parts = []
            
            for page_num, image in enumerate(images, 1):
                # Apply OCR to each page
                page_text = pytesseract.image_to_string(image)
                if page_text:
                    text_parts.append(f"--- Page {page_num} ---\n{page_text}")
                    
                # Clean up image
                image.close()
            
            return "\n".join(text_parts)
        except Exception as e:
            logger.warning(f"OCR text extraction failed: {str(e)}")
            return ""

    def get_pdf_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from PDF
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary containing PDF metadata
        """
        try:
            metadata = {
                "file_size_mb": os.path.getsize(file_path) / (1024 * 1024),
                "created_at": datetime.fromtimestamp(os.path.getctime(file_path)),
                "modified_at": datetime.fromtimestamp(os.path.getmtime(file_path)),
                "num_pages": 0,
            }
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata["num_pages"] = len(pdf_reader.pages)
                
                if pdf_reader.metadata:
                    metadata["pdf_metadata"] = {
                        "title": pdf_reader.metadata.get("/Title"),
                        "author": pdf_reader.metadata.get("/Author"),
                        "subject": pdf_reader.metadata.get("/Subject"),
                        "creator": pdf_reader.metadata.get("/Creator"),
                    }
            
            return metadata
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {str(e)}")
            return {"error": str(e)}

    def parse_feedback_from_text(self, text: str, feedback_type: str) -> Dict[str, str]:
        """
        Parse structured feedback sections from extracted text
        
        Args:
            text: Extracted text from PDF
            feedback_type: Type of feedback ("company_function", "self_feedback", "project_feedback")
            
        Returns:
            Dictionary with parsed sections
        """
        parsed_data = {
            "raw_text": text,
            "certifications": "",
            "learning": "",
            "project_activity": "",
            "project_responsibilities": "",
            "key_contributions": "",
            "function_activity": "",
            "function_contributions": "",
        }
        
        try:
            # Define section keywords based on feedback type
            section_keywords = self._get_section_keywords(feedback_type)
            
            # Search for and extract sections
            text_lower = text.lower()
            for section_name, keywords in section_keywords.items():
                for keyword in keywords:
                    keyword_lower = keyword.lower()
                    if keyword_lower in text_lower:
                        # Find content after keyword
                        idx = text_lower.find(keyword_lower)
                        if idx != -1:
                            # Extract next 500 characters as section content
                            content = text[idx + len(keyword):idx + len(keyword) + 500].strip()
                            if content:
                                parsed_data[section_name] = content
                                break
        except Exception as e:
            logger.error(f"Error parsing feedback sections: {str(e)}")
        
        return parsed_data

    @staticmethod
    def _get_section_keywords(feedback_type: str) -> Dict[str, list]:
        """Get section keywords for each feedback type"""
        base_keywords = {
            "certifications": ["certification", "certificate", "licensed", "qualified"],
            "learning": ["learning", "training", "development", "course", "education"],
            "key_contributions": ["contribution", "achieved", "accomplished", "delivered"],
        }
        
        if feedback_type == "project_feedback":
            base_keywords.update({
                "project_activity": ["project activity", "project involvement", "project work"],
                "project_responsibilities": ["responsibility", "responsibility for", "responsible for"],
            })
        elif feedback_type == "company_function":
            base_keywords.update({
                "function_activity": ["function activity", "team activity", "department role"],
                "function_contributions": ["function contribution", "team contribution", "role contribution"],
            })
        
        return base_keywords

    def cleanup_temp_files(self, file_path: str):
        """Clean up temporary files during processing"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Error cleaning up file {file_path}: {str(e)}")
