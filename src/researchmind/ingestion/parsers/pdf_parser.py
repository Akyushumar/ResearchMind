import asyncio
from pathlib import Path
import fitz  # PyMuPDF

from researchmind.config.logging import get_logger
from researchmind.ingestion.base import (
    DocumentParser,
    PageContent,
    ParsedDocument,
    TextBlock,
)

logger = get_logger(__name__)


class PDFParser(DocumentParser):
    """PDF document parser using PyMuPDF."""

    def supported_extensions(self) -> list[str]:
        return [".pdf"]

    async def parse(self, file_path: Path) -> ParsedDocument:
        """Parse a PDF file into pages with text blocks and bounding boxes."""
        return await asyncio.to_thread(self._parse_sync, file_path)

    def _parse_sync(self, file_path: Path) -> ParsedDocument:
        logger.info("pdf_parser_started", file_path=str(file_path))
        doc = fitz.open(str(file_path))
        
        pages = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            width = page.rect.width
            height = page.rect.height
            
            blocks = []
            dict_data = page.get_text("dict")
            for block_index, b in enumerate(dict_data.get("blocks", [])):
                if b.get("type") == 0:  # Text block
                    bbox = b.get("bbox", [0, 0, 0, 0])
                    # Combine all text in block
                    text_parts = []
                    font_size = None
                    font_name = None
                    is_bold = False
                    
                    for line in b.get("lines", []):
                        for span in line.get("spans", []):
                            text_parts.append(span.get("text", ""))
                            if font_size is None:
                                font_size = span.get("size")
                                font_name = span.get("font")
                                font_flags = span.get("flags", 0)
                                is_bold = bool(font_flags & 2**4)
                                
                    text = "".join(text_parts).strip()
                    if text:
                        blocks.append(
                            TextBlock(
                                text=text,
                                page_number=page_num + 1,
                                block_index=block_index,
                                x0=bbox[0],
                                y0=bbox[1],
                                x1=bbox[2],
                                y1=bbox[3],
                                font_size=font_size,
                                font_name=font_name,
                                is_bold=is_bold,
                            )
                        )
            
            pages.append(
                PageContent(
                    page_number=page_num + 1,
                    text=page.get_text("text").strip(),
                    width=width,
                    height=height,
                    blocks=blocks,
                )
            )

        metadata = doc.metadata
        doc.close()
        
        logger.info("pdf_parser_completed", file_path=str(file_path), total_pages=len(pages))
        
        return ParsedDocument(
            file_path=str(file_path),
            pages=pages,
            total_pages=len(pages),
            metadata=metadata,
        )
