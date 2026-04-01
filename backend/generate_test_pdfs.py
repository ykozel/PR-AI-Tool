"""
Script to generate all test PDF files for the upload API
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime

def get_custom_styles():
    """Return custom paragraph styles"""
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor('#2e5c8a'),
        spaceAfter=10,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        leading=14,
        alignment=4,
    )
    
    return title_style, heading_style, body_style

def create_header_table(employee_name, dept, role):
    """Create employee information header table"""
    employee_data = [
        ['Employee Name:', employee_name, 'Period:', 'January - December 2025'],
        ['Department:', dept, 'Role:', role],
        ['Review Date:', datetime.now().strftime('%B %d, %Y'), '', ''],
    ]
    
    table = Table(employee_data, colWidths=[1.2*inch, 1.8*inch, 1.2*inch, 1.8*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0f7')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#e8f0f7')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    return table

def create_project_feedback_pdf(filename):
    """Create Project Feedback PDF with all 6 mandatory sections"""
    doc = SimpleDocTemplate(filename, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    title_style, heading_style, body_style = get_custom_styles()
    story = []
    
    story.append(Paragraph("PROJECT FEEDBACK FORM - ANNUAL REVIEW 2025", title_style))
    story.append(create_header_table("John Smith", "Engineering", "Lead Software Architect"))
    story.append(Spacer(1, 0.3*inch))
    
    # Section 1: Previous Year Link
    story.append(Paragraph("1. PREVIOUS YEAR LINK", heading_style))
    previous_year = """
    Reference: 2024 Annual Review - Employee ID: EMP-2024-001456
    Prior Year Performance Rating: Exceeds Expectations (4.2/5)
    Key Achievements: Led microservices migration, reduced system latency by 45%, mentored 2 engineers to promotion
    """
    story.append(Paragraph(previous_year, body_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Section 2: Certifications
    story.append(Paragraph("2. CERTIFICATIONS", heading_style))
    certifications = """
    <b>Current Certifications:</b>
    <br/>- AWS Solutions Architect Professional (renewed Jan 2025, expires 2027)
    <br/>- Certified Kubernetes Administrator (CKA) - issued Mar 2024
    <br/>- Google Cloud Professional Data Engineer - issued Jun 2024
    <br/>- Certified Information Systems Security Professional (CISSP) - renewed Dec 2024
    <br/><br/>
    <b>In Progress:</b> AWS Solutions Architect Expert, Cloud Security Certification
    <br/><b>Total Certifications:</b> 8 current certifications
    """
    story.append(Paragraph(certifications, body_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Section 3: Learning
    story.append(Paragraph("3. LEARNING & DEVELOPMENT", heading_style))
    learning = """
    <b>Professional Development Completed:</b>
    <br/>- Advanced Kubernetes Administration Course (24 hours, Mar 2025)
    <br/>- Cloud Architecture Best Practices Workshop (16 hours, Feb 2025)
    <br/>- AI/ML for Cloud Infrastructure (32 hours, completed May 2025)
    <br/>- Leadership and Team Development Program (40 hours, ongoing)
    <br/><br/>
    <b>Skills Acquired:</b> Advanced Kubernetes patterns, ML Ops fundamentals, architectural design principles
    <br/><b>Total Development Hours:</b> 180 hours in 2025
    """
    story.append(Paragraph(learning, body_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Section 4: Feedback
    story.append(Paragraph("4. PERFORMANCE FEEDBACK", heading_style))
    feedback = """
    <b>Manager Assessment:</b> John demonstrates exceptional technical leadership and strategic vision. Consistently delivers 
    high-quality solutions and effectively mentors team members. Shows excellent problem-solving skills and proactive approach to 
    challenges. Communication skills are strong and he collaborates well cross-functionally.
    <br/><br/>
    <b>Peer Feedback:</b> Highly respected by colleagues for technical expertise and willingness to help. Creates inclusive team 
    environment and shares knowledge generously. Demonstrates commitment to continuous improvement.
    <br/><br/>
    <b>Overall Rating:</b> Exceeds Expectations (4.3/5.0) - Promotable
    """
    story.append(Paragraph(feedback, body_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Section 5: Project Activity
    story.append(Paragraph("5. PROJECT ACTIVITY & CONTRIBUTIONS", heading_style))
    responsibilities = """
    <b>Cloud Migration Initiative - Lead Architect</b> (Jan-Jun 2025)
    <br/>Designed and executed cloud migration strategy for 45+ enterprise applications. Managed cross-functional team of 8 engineers, 
    coordinated with stakeholders, and managed $2.5M project budget. Achieved zero-downtime migration, reduced infrastructure costs 35%, 
    improved system scalability 4x.
    <br/><br/>
    <b>Key Project Contributions:</b>
    <br/>- Architected microservices infrastructure reducing deployment time from 4 hours to 15 minutes
    <br/>- Implemented disaster recovery plan achieving 99.99% uptime SLA with 100% recovery success
    <br/>- Led security framework achieving 100% compliance audit score
    <br/>- Mentored 3 junior engineers leading to 2 promotions
    <br/>- Conducted 12 technical workshops training 80+ staff members
    <br/>- Project ROI: 180% with $4.5M annual cost savings
    """
    story.append(Paragraph(responsibilities, body_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Section 6: Function Activity
    story.append(Paragraph("6. FUNCTION ACTIVITY - COMMITTEE PARTICIPATION", heading_style))
    function = """
    <b>Technical Excellence Committee - Lead/Co-Chair</b>
    <br/>Organized and led monthly technical forum with 25+ participants discussing architectural innovations and best practices. 
    Established knowledge-sharing program with monthly sessions. Created technical standards documentation used across organization.
    <br/><br/>
    <b>Architecture Review Board - Active Member</b> (8 reviews conducted in 2025)
    <br/>Reviewed and approved major architectural decisions for company projects. Provided mentoring and guidance to engineering teams 
    on architectural patterns and best practices. Successfully guided 8 projects toward optimal technical solutions.
    <br/><br/>
    <b>Involvement Level:</b> Lead - Significant responsibility and visibility
    """
    story.append(Paragraph(function, body_style))
    
    doc.build(story)
    print(f"✅ Created: {filename}")

def create_company_function_feedback_pdf(filename):
    """Create Company Function Feedback PDF with all 6 mandatory sections"""
    doc = SimpleDocTemplate(filename, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    title_style, heading_style, body_style = get_custom_styles()
    story = []
    
    story.append(Paragraph("COMPANY FUNCTION FEEDBACK FORM - ANNUAL REVIEW 2025", title_style))
    story.append(create_header_table("Sarah Johnson", "Operations", "Operations Manager"))
    story.append(Spacer(1, 0.3*inch))
    
    # Section 1: Previous Year Link
    story.append(Paragraph("1. PREVIOUS YEAR LINK", heading_style))
    previous_year = """
    Reference: 2024 Annual Review - Employee ID: EMP-2024-002789
    Prior Year Performance Rating: Meets Expectations (3.8/5)
    Key Achievements: Improved process efficiency by 20%, led operations team restructuring, achieved cost savings of $500K
    """
    story.append(Paragraph(previous_year, body_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Section 2: Certifications
    story.append(Paragraph("2. CERTIFICATIONS & QUALIFICATIONS", heading_style))
    certifications = """
    <b>Professional Certifications:</b>
    <br/>- Lean Six Sigma Black Belt (issued Jan 2023, active)
    <br/>- Project Management Professional (PMP) - issued Jun 2022, expires Jun 2025 (renewal planned)
    <br/>- ISO 9001:2015 Quality Management Systems Lead Auditor (issued Apr 2024)
    <br/>- Certified Operations Manager (COM) - issued Nov 2024
    <br/><br/>
    <b>Specialized Training Completed:</b> Change Management, Strategic Operations Planning, Risk Management
    <br/><b>Total Certifications:</b> 4 active professional certifications
    """
    story.append(Paragraph(certifications, body_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Section 3: Learning
    story.append(Paragraph("3. LEARNING & PROFESSIONAL DEVELOPMENT", heading_style))
    learning = """
    <b>Training Programs Completed:</b>
    <br/>- Advanced Process Improvement Techniques (32 hours, Feb 2025)
    <br/>- Digital Transformation for Operations Managers (24 hours, Mar 2025)
    <br/>- Strategic Supply Chain Management (40 hours, Apr-May 2025)
    <br/>- Executive Leadership Program (60 hours, ongoing through Dec 2025)
    <br/><br/>
    <b>Skills Developed:</b> Advanced data analytics, process automation, strategic planning, digital tool implementation
    <br/><b>Professional Development Investment:</b> 200+ hours in 2025
    """
    story.append(Paragraph(learning, body_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Section 4: Feedback
    story.append(Paragraph("4. PERFORMANCE FEEDBACK & ASSESSMENT", heading_style))
    feedback = """
    <b>Manager Assessment:</b> Sarah demonstrates strong operational leadership and commitment to continuous improvement. Effectively 
    manages complex operations, drives process optimization initiatives, and maintains high team morale. Shows excellent problem-solving 
    abilities and strategic thinking. Communication and collaboration skills are excellent.
    <br/><br/>
    <b>Peer Feedback:</b> Recognized as reliable and detail-oriented leader who fosters collaborative team environment. Team members 
    appreciate her mentoring approach and clear communication. Cross-functional partners value her proactive approach to problem-solving.
    <br/><br/>
    <b>Overall Rating:</b> Exceeds Expectations (4.1/5.0) - Ready for Senior Operations Role
    """
    story.append(Paragraph(feedback, body_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Section 5: Project Activity
    story.append(Paragraph("5. PROJECT ACTIVITY & OPERATIONAL ACHIEVEMENTS", heading_style))
    project_activity = """
    <b>Operations Excellence Initiative - Project Lead</b> (Jan-Dec 2025)
    <br/>Led comprehensive operations transformation project impacting 5 departments with 120+ employees. Implemented lean methodology, 
    process automation, and KPI monitoring system. Achieved 30% efficiency improvement and $750K annual cost reduction.
    <br/><br/>
    <b>Key Project Contributions:</b>
    <br/>- Designed and implemented new operational workflow reducing processing time by 40%
    <br/>- Implemented operations management software improving visibility and reporting accuracy
    <br/>- Established quality metrics framework achieving 98% quality score
    <br/>- Led 3 major process reengineering projects affecting 85+ staff
    <br/>- Developed comprehensive risk management plan reducing operational risks by 45%
    <br/>- Project ROI: 250% with multi-year cost savings exceeding $2M
    """
    story.append(Paragraph(project_activity, body_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Section 6: Function Activity
    story.append(Paragraph("6. FUNCTION ACTIVITY - OPERATIONAL COMMITTEE", heading_style))
    function_activity = """
    <b>Operations Excellence Committee - Lead/Co-Chair</b>
    <br/>Established and chairs monthly operations excellence forum with 20+ department leaders discussing best practices, 
    efficiency improvements, and operational challenges. Created operations standards documentation used across all departments. 
    Led quarterly operational reviews for all business units.
    <br/><br/>
    <b>Cross-Functional Process Improvement Team - Active Member</b>
    <br/>Participated in 6 cross-departmental improvement initiatives throughout 2025. Provided operational expertise and guidance to 
    marketing, sales, and customer success teams. Successfully implemented 4 operational recommendations improving company-wide efficiency.
    <br/><br/>
    <b>Involvement Level:</b> Lead - Strategic responsibility for company-wide operations excellence
    """
    story.append(Paragraph(function_activity, body_style))
    
    doc.build(story)
    print(f"✅ Created: {filename}")

def create_self_feedback_pdf(filename):
    """Create Self Feedback Form PDF with all 6 mandatory sections"""
    doc = SimpleDocTemplate(filename, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    title_style, heading_style, body_style = get_custom_styles()
    story = []
    
    story.append(Paragraph("SELF ASSESSMENT FORM - ANNUAL REVIEW 2025", title_style))
    story.append(create_header_table("Michael Chen", "Product Development", "Senior Product Manager"))
    story.append(Spacer(1, 0.3*inch))
    
    # Section 1: Previous Year Link
    story.append(Paragraph("1. PREVIOUS YEAR LINK & PROGRESS", heading_style))
    previous_year = """
    Reference: 2024 Annual Review - Employee ID: EMP-2024-003421
    Prior Year Performance Rating: Exceeds Expectations (4.0/5)
    Goals from 2024: Launch 2 new products, increase customer satisfaction, build product analytics capability
    Status: All goals exceeded with 3 products launched, satisfaction increased to 8.5/10
    """
    story.append(Paragraph(previous_year, body_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Section 2: Certifications
    story.append(Paragraph("2. PROFESSIONAL CERTIFICATIONS", heading_style))
    certifications = """
    <b>Current Certifications:</b>
    <br/>- Certified Scrum Product Owner (CSPO) - renewed May 2025, expires May 2027
    <br/>- AWS Solutions Architect Associate - issued Sep 2024, expires Sep 2026
    <br/>- Project Management Professional (PMP) - renewed Nov 2024, expires Nov 2027
    <br/>- Google Analytics Individual Qualification (GAIQ) - issued Feb 2025
    <br/>- Scaled Agile Certified Program Consultant (SAFe 6.0) - issued Mar 2025
    <br/><br/>
    <b>Certifications in Progress:</b> Advanced Analytics, Product Strategy & Leadership
    <br/><b>Total Active Certifications:</b> 5 professional certifications with 2 in progress
    """
    story.append(Paragraph(certifications, body_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Section 3: Learning
    story.append(Paragraph("3. LEARNING & GROWTH ACCOMPLISHMENTS", heading_style))
    learning = """
    <b>Professional Development Completed:</b>
    <br/>- Advanced Product Analytics & Predictive Modeling (40 hours, Jan-Feb 2025)
    <br/>- AI/ML Applications in Product Development (32 hours, Mar-Apr 2025)
    <br/>- Executive Product Management Program (60 hours, May-Jun 2025)
    <br/>- Data Science Fundamentals for Product Managers (24 hours, Jul 2025)
    <br/>- Market Research & Competitive Intelligence (20 hours, Aug 2025)
    <br/><br/>
    <b>Skills Developed:</b> Advanced analytics, ML fundamentals, market analysis, predictive modeling, AI applications
    <br/><b>Conferences Attended:</b> ProductCon USA, SaaS Canada, AI Summit 2025 (3 major conferences)
    <br/><b>Total Development Investment:</b> 180+ hours of professional education in 2025
    <br/><br/>
    <b>Key Learning Outcomes:</b>
    <br/>- Implemented predictive analytics reducing feature development risk by 35%
    <br/>- Led knowledge transfer sessions on AI/ML to 25+ team members
    <br/>- Mentored 2 junior product managers contributing to their career development
    <br/>- Contributed to company product management curriculum and technical training
    """
    story.append(Paragraph(learning, body_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Section 4: Self-Feedback
    story.append(Paragraph("4. PERSONAL PERFORMANCE ASSESSMENT", heading_style))
    feedback = """
    <b>Self-Assessment:</b> 2025 was a highly successful year marked by significant product achievements and personal growth. 
    I successfully led product strategy initiatives, delivered new products to market, and expanded my technical competencies. 
    Notably improved my analytical capabilities and gained deeper understanding of AI/ML applications in product management.
    <br/><br/>
    <b>Strengths Demonstrated:</b>
    <br/>- Strategic thinking and product vision clarity
    <br/>- Data-driven decision making and analytical skills
    <br/>- Team leadership and mentoring capabilities
    <br/>- Cross-functional collaboration and communication
    <br/>- Continuous learning mindset and adaptability
    <br/><br/>
    <b>Areas for Growth:</b> Further develop enterprise sales understanding, improve public speaking skills at larger audiences
    <br/><br/>
    <b>Self-Rating:</b> Exceeds Expectations (4.2/5.0) - Ready for VP Product role
    """
    story.append(Paragraph(feedback, body_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Section 5: Project Activity
    story.append(Paragraph("5. PROJECT ACTIVITY & PRODUCT ACHIEVEMENTS", heading_style))
    project_activity = """
    <b>Product Launch Initiative - Lead Product Manager</b> (Jan-Dec 2025)
    <br/>Led cross-functional team of 15+ people (engineering, design, marketing, operations) through 3 major product launches. 
    Managed $5M product budget, conducted market research, defined product requirements, and coordinated go-to-market strategy. 
    All products launched on schedule within budget generating $2.5M+ in first-year revenue.
    <br/><br/>
    <b>Key Project Contributions:</b>
    <br/>- Increased customer satisfaction score from 7.2 to 8.5 (18% improvement)
    <br/>- Successfully launched 3 new products generating $2.5M in revenue
    <br/>- Improved product launch cycle time by 40% (from 6 months to 3.6 months)
    <br/>- Built high-performing product team with 95% retention rate and 1 internal promotion
    <br/>- Established market research program reducing feature development risk by 35%
    <br/>- Conducted 8 customer research sessions influencing 12 product decisions
    <br/>- Project ROI: 220% with projected 2-year revenue of $6M+
    """
    story.append(Paragraph(project_activity, body_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Section 6: Function Activity
    story.append(Paragraph("6. FUNCTION ACTIVITY - PRODUCT LEADERSHIP", heading_style))
    function_activity = """
    <b>Product Council - Active Member & Advisor</b>
    <br/>Served on product council with 8 product leaders providing strategic guidance on company product direction. 
    Contributed to quarterly product strategy reviews, participated in roadmap prioritization, and provided technical 
    expertise on AI/ML product integration. Attended 12 quarterly council meetings.
    <br/><br/>
    <b>Product Excellence Initiative - Co-Lead</b> (Mar-Dec 2025)
    <br/>Co-led company-wide product excellence initiative improving product quality and customer success metrics. Established 
    product quality metrics and monitoring framework. Coordinated with all product teams implementing 5 quality improvement initiatives. 
    Improved overall product quality score by 25%.
    <br/><br/>
    <b>University Mentoring Program - Program Mentor</b>
    <br/>Mentored 4 MBA students from leading universities providing practical product management guidance. Co-created product 
    management curriculum used in university business programs. Conducted 8 guest lectures on product strategy and analytics to 120+ students.
    <br/><br/>
    <b>Involvement Level:</b> Lead - Strategic visibility and significant responsibility for company product direction
    """
    story.append(Paragraph(function_activity, body_style))
    
    doc.build(story)
    print(f"✅ Created: {filename}")

if __name__ == "__main__":
    print("Generating test PDF files...")
    create_project_feedback_pdf("Project_Feedback.pdf")
    create_company_function_feedback_pdf("Company_Function_Feedback.pdf")
    create_self_feedback_pdf("Self_Feedback.pdf")
    print("\n✨ All test PDFs created successfully!")
