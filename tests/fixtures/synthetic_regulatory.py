import fitz
from pathlib import Path

def create_synthetic_dcr_pdf(path: Path) -> Path:
    """Creates a synthetic regulatory PDF matching UDCPR Chapter 8 structure."""
    doc = fitz.open()
    
    # --- Page 1 ---
    page1 = doc.new_page()
    y = 50
    # Chapter heading (Level 0)
    page1.insert_text(fitz.Point(50, y), "CHAPTER 8 – PARKING, LOADING AND UNLOADING SPACES", fontname="hebo", fontsize=16)
    y += 50
    
    # Section heading (Level 1)
    page1.insert_text(fitz.Point(50, y), "8.1 General", fontname="hebo", fontsize=13)
    y += 30
    page1.insert_text(fitz.Point(50, y), "This section deals with general parking guidelines.", fontname="helv", fontsize=11)
    y += 40
    
    # Section heading (Level 1)
    page1.insert_text(fitz.Point(50, y), "8.2 Parking Requirements", fontname="hebo", fontsize=13)
    y += 30
    page1.insert_text(fitz.Point(50, y), "The parking spaces shall provide as per Regulation 6.3.", fontname="helv", fontsize=11)
    y += 40
    
    # Subsection heading (Level 2/3 decimal)
    page1.insert_text(fitz.Point(50, y), "8.2.1 Residential Buildings", fontname="hebo", fontsize=11)
    y += 30
    
    # Lettered items
    page1.insert_text(fitz.Point(50, y), "(a) Buildings up to 15m in height shall have surface parking.", fontname="helv", fontsize=11)
    y += 30
    page1.insert_text(fitz.Point(50, y), "(b) Buildings above 15m in height shall have:", fontname="helv", fontsize=11)
    y += 30
    
    # Roman items
    page1.insert_text(fitz.Point(70, y), "(i) Fire safety provisions.", fontname="helv", fontsize=11)
    y += 30
    page1.insert_text(fitz.Point(70, y), "(ii) Adequate water supply.", fontname="helv", fontsize=11)
    y += 40
    
    # Proviso (Bold keyword, but body text size)
    page1.insert_text(fitz.Point(50, y), "Provided that in areas where space is constrained, this may be permitted.", fontname="hebo", fontsize=11)
    y += 40
    
    # Note
    page1.insert_text(fitz.Point(50, y), "Note: Stack parking may be permitted subject to provisions of Regulation 8.1.", fontname="hebo", fontsize=11)
    y += 40
    
    page1.insert_text(fitz.Point(50, y), "For more details, refer Table 8-B.", fontname="helv", fontsize=11)
    
    # --- Page 2 ---
    page2 = doc.new_page()
    y = 50
    
    # Subsection (continuation of siblings)
    page2.insert_text(fitz.Point(50, y), "8.2.2 Commercial Buildings", fontname="hebo", fontsize=11)
    y += 30
    page2.insert_text(fitz.Point(50, y), "Commercial buildings must comply with Table 8-B.", fontname="helv", fontsize=11)
    y += 50
    
    # Table label
    page2.insert_text(fitz.Point(50, y), "Table 8-B", fontname="hebo", fontsize=11)
    y += 30
    
    # Table headers
    page2.insert_text(fitz.Point(50, y), "Occupancy", fontname="hebo", fontsize=11)
    page2.insert_text(fitz.Point(150, y), "Floor Area", fontname="hebo", fontsize=11)
    page2.insert_text(fitz.Point(250, y), "Required ECS", fontname="hebo", fontsize=11)
    y += 20
    
    # Table row 1
    page2.insert_text(fitz.Point(50, y), "Residential", fontname="helv", fontsize=11)
    page2.insert_text(fitz.Point(150, y), "100 sq.m", fontname="helv", fontsize=11)
    page2.insert_text(fitz.Point(250, y), "1", fontname="helv", fontsize=11)
    y += 20
    
    # Table row 2
    page2.insert_text(fitz.Point(50, y), "Commercial", fontname="helv", fontsize=11)
    page2.insert_text(fitz.Point(150, y), "100 sq.m", fontname="helv", fontsize=11)
    page2.insert_text(fitz.Point(250, y), "2", fontname="helv", fontsize=11)
    
    # --- Page 3 ---
    page3 = doc.new_page()
    page3.insert_text(fitz.Point(50, 50), "8.3 Future expansion", fontname="hebo", fontsize=13)
    page3.insert_text(fitz.Point(50, 80), "This is a test section on page 3.", fontname="helv", fontsize=11)
    
    doc.save(path)
    doc.close()
    return path
