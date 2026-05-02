"""
Upload Routes - File upload, listing, retrieval, and deletion
"""
import os
import hashlib
import re
import tempfile
import mimetypes
import logging
from datetime import datetime
from pathlib import Path
from collections import Counter

from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from app.models import db
from app.models.document import Document, FileMetadata
from app.models.audit_log import AuditLog
from app.utils.validators import validate_filename, validate_file_extension, sanitize_input
from app.utils.text_extractor import TextExtractor, TextPreprocessor
from app.utils.entity_extractor import EntityExtractor
from app.utils.classifier import DocumentClassifier
from app.utils.file_storage import FileStorage
from app.utils.attribute_extractor import AttributeExtractor

logger = logging.getLogger(__name__)

upload_bp = Blueprint('upload', __name__, url_prefix='/api')

# Module-level classifier (loaded lazily)
_classifier: DocumentClassifier | None = None


def _get_classifier() -> DocumentClassifier:
    global _classifier
    if _classifier is None:
        _classifier = DocumentClassifier()
        _classifier.load()
    return _classifier


def _get_storage() -> FileStorage:
    return FileStorage(
        upload_root=current_app.config['UPLOAD_FOLDER'],
        encryption_key=current_app.config['ENCRYPTION_KEY'],
    )


def _mutate_file_hash(doc: Document) -> None:
    seed = f"{doc.file_hash}-{datetime.utcnow().isoformat()}-{os.urandom(8).hex()}"
    doc.file_hash = hashlib.sha256(seed.encode('utf-8')).hexdigest()


def _format_entity_keywords(entities: dict) -> str | None:
    persons = entities.get('persons', []) if entities else []
    orgs = entities.get('orgs', []) if entities else []
    parts = []
    for p in persons[:5]:
        parts.append(f"person:{p}")
    for o in orgs[:5]:
        parts.append(f"org:{o}")
    if not parts:
        return None
    joined = ', '.join(parts)
    return joined[:500]


def _allowed_file(filename: str) -> bool:
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return ext in current_app.config.get('ALLOWED_EXTENSIONS', set())


def _log_audit(user_id: int, action: str, resource: str,
               resource_id: int | None, status: str,
               detail: str, ip: str):
    try:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource,
            resource_id=resource_id,
            resource_name=detail,
            status=status,
            ip_address=ip,
        )
        db.session.add(entry)
        db.session.commit()
    except Exception as e:
        logger.warning(f"Audit log failed: {e}")


# ── Image extensions ───────────────────────────────────────────────────────
_IMAGE_EXTS = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'tif', 'svg'}

# ── Gallery context keywords (filename/content → specific gallery folder name)
_GALLERY_CONTEXTS = [
    (['school', 'classroom', 'teacher', 'student', 'blackboard', 'uniform'],  'School Gallery'),
    (['college', 'campus', 'hostel', 'canteen', 'fest', 'university'],        'College Gallery'),
    (['office', 'workspace', 'desk', 'meeting room', 'conference'],           'Office Gallery'),
    (['wedding', 'bride', 'groom', 'ceremony', 'reception', 'marriage'],      'Wedding Gallery'),
    (['birthday', 'cake', 'celebration', 'party', 'anniversary'],             'Birthday Gallery'),
    (['family', 'parents', 'siblings', 'relatives', 'reunion'],               'Family Gallery'),
    (['travel', 'trip', 'tour', 'vacation', 'holiday', 'tourist', 'flight'],  'Travel Gallery'),
    (['nature', 'forest', 'mountain', 'beach', 'river', 'landscape', 'sky'], 'Nature Gallery'),
    (['food', 'restaurant', 'dish', 'meal', 'recipe', 'cafe', 'kitchen'],     'Food Gallery'),
    (['product', 'item', 'shop', 'ecommerce', 'store', 'catalog'],            'Product Gallery'),
    (['screenshot', 'screen', 'capture', 'snap', 'desktop'],                  'Screenshots'),
    (['logo', 'brand', 'icon', 'banner', 'poster', 'flyer', 'design'],        'Design Assets'),
    (['profile', 'selfie', 'portrait', 'headshot', 'avatar'],                 'Profile Photos'),
    (['event', 'function', 'ceremony', 'inauguration', 'launch', 'program'],  'Event Photos'),
    (['sports', 'cricket', 'football', 'match', 'tournament', 'athlete'],     'Sports Gallery'),
    (['medical', 'xray', 'scan', 'report', 'hospital', 'doctor'],             'Medical Images'),
]

# ── Ordered document classification rules (phrase → folder) ────────────────
# Checked strictly in order — FIRST match wins. Put most specific rules first.
_DOC_RULES = [
    # ── BITFLOW (highest priority when present) ─────────────────────────
    (['bitflow', 'bit flow', 'bit-flow'],                                     'Bitflow'),
    # ── CERTIFICATES (checked first — single word too) ────────────────────
    (['certificate of', 'this is to certify', 'certify that', 'awarded to',
      'in recognition of', 'successfully completed', 'completion certificate',
      'certification', 'has been awarded', 'is hereby awarded',
      'course completion', 'training completion'],                             'Certificates'),
    # Single word 'certificate' — kept HIGH, before legal, before anything else
    (['certificate'],                                                          'Certificates'),
    # ── IDENTITY ──────────────────────────────────────────────────────────
    (['aadhaar', 'aadhar', 'voter id', 'driving licence', 'driving license',
      'passport number', 'pan card', 'identity card', 'id card'],              'Identity Documents'),
    # ── PAYSLIPS ──────────────────────────────────────────────────────────
    (['salary slip', 'pay slip', 'payslip', 'gross salary', 'net salary',
      'net pay', 'basic pay', 'employee id', 'epf', 'esi deduction'],          'Payslips'),
    # ── OFFER LETTERS ─────────────────────────────────────────────────────
    (['offer letter', 'appointment letter', 'joining date', 'designation',
      'ctc', 'cost to company', 'probation period', 'date of joining'],        'Offer Letters'),
    # ── RESUMES ───────────────────────────────────────────────────────────
    (['career objective', 'professional summary', 'work experience',
      'curriculum vitae', 'skills summary', 'key skills'],                     'Resume'),
    (['resume', 'cv'],                                                         'Resume'),
    # ── INVOICES ──────────────────────────────────────────────────────────
    (['invoice no', 'invoice number', 'bill no', 'amount due',
      'total amount', 'subtotal', 'cgst', 'sgst', 'igst', 'billing address'],  'Invoices'),
    (['invoice', 'bill'],                                                      'Invoices'),
    # ── RECEIPTS ──────────────────────────────────────────────────────────
    (['receipt no', 'payment received', 'received with thanks',
      'cash receipt', 'amount received'],                                       'Receipts'),
    # ── TAX ───────────────────────────────────────────────────────────────
    (['income tax', 'itr', 'form 16', 'tds certificate', 'acknowledgement number',
      'assessment year', 'gst number', 'gstin', 'tax invoice'],                'Tax Documents'),
    (['tax', 'gst', 'vat', 'itr'],                                             'Tax Documents'),
    # ── BANK ──────────────────────────────────────────────────────────────
    (['account number', 'ifsc code', 'bank statement', 'opening balance',
      'closing balance', 'passbook', 'cheque', 'neft', 'rtgs', 'imps'],       'Bank Statements'),
    (['bank', 'account', 'statement'],                                         'Bank Statements'),
    # ── MEDICAL ───────────────────────────────────────────────────────────
    (['patient name', 'diagnosis', 'prescription', 'tablet', 'capsule',
      'dosage', 'laboratory report', 'blood test', 'haemoglobin'],             'Medical'),
    (['medical', 'hospital', 'doctor'],                                        'Medical'),
    # ── INSURANCE ─────────────────────────────────────────────────────────
    (['policy number', 'sum insured', 'premium amount', 'insured name',
      'nominee', 'maturity date'],                                              'Insurance'),
    (['insurance', 'premium'],                                                 'Insurance'),
    # ── ACADEMIC / MARKSHEETS ─────────────────────────────────────────────
    (['marksheet', 'mark sheet', 'grade sheet', 'semester result',
      'roll number', 'admit card', 'hall ticket', 'examination'],              'Academic'),
    (['school', 'college', 'university'],                                      'Academic'),
    # ── TRAINING / LMS ────────────────────────────────────────────────────
    (['learning management', 'lms', 'e-learning', 'training module',
      'course outline', 'training material', 'workshop agenda'],               'Training'),
    (['training', 'course', 'module', 'learning'],                             'Training'),
    # ── MEETING NOTES ─────────────────────────────────────────────────────
    (['minutes of meeting', 'mom', 'action items', 'attendees present',
      'agenda for', 'next meeting'],                                            'Meeting Notes'),
    (['meeting', 'minutes', 'agenda'],                                         'Meeting Notes'),
    # ── PURCHASE ORDERS ───────────────────────────────────────────────────
    (['purchase order', 'po number', 'delivery date', 'terms of delivery',
      'vendor code', 'procurement'],                                            'Purchase Orders'),
    (['purchase', 'vendor', 'quotation'],                                      'Purchase Orders'),
    # ── PROJECT DOCS ──────────────────────────────────────────────────────
    (['project plan', 'project scope', 'scope of work', 'milestones',
      'deliverables', 'project report'],                                        'Project Documents'),
    (['project', 'milestone', 'deliverable'],                                  'Project Documents'),
    # ── RESEARCH ──────────────────────────────────────────────────────────
    (['abstract', 'methodology', 'literature review', 'bibliography',
      'research paper', 'hypothesis'],                                          'Research Papers'),
    (['report', 'analysis', 'research'],                                       'Reports'),
    # ── FINANCIAL REPORTS ─────────────────────────────────────────────────
    (['balance sheet', 'profit and loss', 'annual report', 'cash flow',
      'financial statement', 'quarterly'],                                      'Financial Reports'),
    # ── HR POLICIES ───────────────────────────────────────────────────────
    (['hr policy', 'leave policy', 'code of conduct', 'employee handbook',
      'disciplinary', 'grievance'],                                             'HR Policies'),
    (['salary', 'payroll', 'employee'],                                        'Payslips'),
    # ── PROPERTY ──────────────────────────────────────────────────────────
    (['sale deed', 'lease agreement', 'rental agreement', 'flat no',
      'survey number', 'property tax', 'stamp duty'],                          'Property Documents'),
    (['property', 'lease', 'rent', 'deed', 'flat'],                            'Property Documents'),
    # ── TECHNICAL / SOFTWARE ──────────────────────────────────────────────
    (['api documentation', 'technical specification', 'system design',
      'software requirement', 'deployment guide', 'user manual'],              'Technical Docs'),
    # ── MARKETING ─────────────────────────────────────────────────────────
    (['marketing plan', 'campaign brief', 'target audience',
      'brand guidelines', 'media plan'],                                        'Marketing'),
    # ── CONTRACTS / LEGAL (last — only matched if nothing above fits) ─────
    (['this agreement', 'entered into agreement', 'hereby agrees',
      'terms and conditions', 'confidentiality agreement', 'nda',
      'non-disclosure', 'indemnify', 'arbitration', 'jurisdiction'],           'Contracts'),
    (['contract', 'agreement'],                                                'Contracts'),
    (['legal notice', 'court order', 'judgment', 'plaintiff', 'defendant',
      'affidavit', 'petition', 'advocate', 'writ'],                            'Legal Documents'),
    (['passport', 'aadhaar', 'license', 'voter', 'identity', 'id proof'],      'Identity Documents'),
]

# ── Stop-words ──────────────────────────────────────────────────────────────
_STOP_WORDS = {
    'the','a','an','is','it','in','on','at','to','of','for','and','or','but',
    'with','by','from','as','be','was','are','were','been','have','has','had',
    'do','does','did','will','would','can','could','should','may','might','shall',
    'not','no','so','if','this','that','these','those','i','we','you','he','she',
    'they','my','our','your','his','her','their','its','all','any','more','also',
    'than','into','about','which','when','then','than','there','here','what','how',
    'each','both','through','during','before','after','above','below','between',
    'out','up','down','off','over','under','again','further','once','same','other',
    'such','only','own','too','very','just','because','while','where','who','whom',
    'per','etc','see','use','used','using','get','got','new','one','two','three',
    'page','pages','date','time','name','file','document','documents','section',
    'www','http','https','com','org','net','email','phone','address','number',
    'dear','sincerely','regards','sir','madam','please','thank','thanks','note',
    'complete','completed','completion','overall','total',
    # domain words that would produce meaningless folder names
    'legal','contract','agreement','clause','terms','condition','liability',
    'arbitration','jurisdiction','compliance','general','other','misc','various',
    'certificate','invoice','billing','payment','balance','account','salary',
    'payroll','insurance','premium','property','lease','mortgage','statement',
}


# ── Words that look like names but are actually document/place keywords ─────
_NAME_BLOCKLIST = {
    # document types
    'resume', 'invoice', 'certificate', 'report', 'document', 'agreement',
    'contract', 'statement', 'letter', 'application', 'form', 'receipt',
    'policy', 'record', 'notice', 'order', 'proposal', 'schedule', 'summary',
    'minutes', 'agenda', 'circular', 'memo', 'notification', 'guideline',
    'manual', 'handbook', 'brochure', 'catalog', 'presentation', 'slides',
    'sheet', 'draft', 'final', 'copy', 'original', 'scan', 'scanned',
    'updated', 'revised', 'signed', 'unsigned', 'new', 'old', 'latest',
    'internship', 'offer', 'appointment', 'joining', 'training', 'experience',
    'employment', 'work', 'job', 'position', 'role', 'designation',
    'founder', 'assessment', 'evaluation', 'bitflow',
    # legal / financial terms that would produce bad folder names
    'legal', 'contract', 'agreement', 'clause', 'terms', 'condition',
    'liability', 'arbitration', 'jurisdiction', 'compliance', 'affidavit',
    'judgment', 'petition', 'plaintiff', 'defendant', 'confidential',
    'invoice', 'billing', 'payment', 'balance', 'account', 'salary',
    'payroll', 'insurance', 'premium', 'property', 'lease', 'mortgage',
    'general', 'other', 'misc', 'miscellaneous', 'various', 'combined',
    # organisations / generic places
    'company', 'organization', 'department', 'division', 'branch', 'office',
    'school', 'college', 'university', 'institute', 'hospital', 'clinic',
    'government', 'ministry', 'national', 'international', 'private', 'limited',
    'pvt', 'ltd', 'llp', 'inc', 'corp', 'india', 'delhi', 'mumbai', 'bangalore',
    # common noise words
    'the', 'and', 'for', 'from', 'with', 'our', 'complete', 'pdf', 'doc', 'docx', 'jpg', 'png',
    'image', 'photo', 'picture', 'file', 'scan', 'img', 'copy', 'page',
    'screenshot', 'download', 'upload', 'backup', 'temp', 'test', 'sample',
    # months / dates
    'january','february','march','april','may','june','july','august',
    'september','october','november','december','jan','feb','mar','apr',
    'jun','jul','aug','sep','oct','nov','dec',
    # titles (strip these, keep what follows)
    'mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'sir', 'master',
}

# Regex patterns to extract a person's name from document text
_NAME_FIELD_PATTERNS = [
    # "Name : Rahul Kumar" / "Employee Name: John Smith"
    r'(?:candidate|employee|student|patient|applicant|name|full\s*name|member\s*name)\s*[:\-]\s*([A-Z][a-z]{1,20}(?:\s+[A-Z][a-z]{1,20}){1,3})',
    # "To: Mr. Rahul Kumar" / "Dear Rahul Kumar,"
    r'(?:dear|to)\s+(?:mr\.?|mrs\.?|ms\.?|dr\.?)?\s*([A-Z][a-z]{1,20}(?:\s+[A-Z][a-z]{1,20}){1,2})',
    # "Mr. John Smith" / "Dr. Priya Sharma"
    r'(?:mr\.?|mrs\.?|ms\.?|dr\.?|prof\.?)\s+([A-Z][a-z]{1,20}(?:\s+[A-Z][a-z]{1,20}){1,2})',
    # Certificate style: "awarded to Rahul Kumar"
    r'(?:awarded to|issued to|certify that|this is to certify that|presented to)\s+([A-Z][a-z]{1,20}(?:\s+[A-Z][a-z]{1,20}){1,3})',
    # Salary/ID style: "Name\n  Rahul Kumar" (multiline field)
    r'Name\s*\n\s*([A-Z][a-z]{1,20}(?:\s+[A-Z][a-z]{1,20}){1,3})',
    # Single-name variants (explicit fields only)
    r'(?:candidate|employee|student|patient|applicant|name|full\s*name|member\s*name)\s*[:\-]\s*([A-Za-z]{2,20})',
    r'(?:dear|to)\s+(?:mr\.?|mrs\.?|ms\.?|dr\.?)?\s*([A-Za-z]{2,20})',
    r'(?:awarded to|issued to|certify that|this is to certify that|presented to)\s+([A-Za-z]{2,20})',
    r'Name\s*\n\s*([A-Za-z]{2,20})',
]

# Filename/content hints that usually indicate personal documents
_PERSONAL_MARKERS = {
    'resume', 'cv', 'certificate', 'assessment', 'offer', 'appointment',
    'joining', 'payslip', 'salary', 'id', 'profile', 'photo', 'internship',
    'evaluation', 'experience', 'founder', 'student', 'candidate',
}

# Folder keywords to ignore for matching (avoid generic buckets)
_FOLDER_MATCH_STOP = {
    'our', 'complete', 'completed', 'completion', 'files', 'file', 'docs',
    'documents', 'document', 'misc', 'general', 'other', 'others', 'all',
    'new', 'old', 'latest', 'updated', 'final', 'draft',
}


def _extract_person_name(filename: str, raw_text: str) -> str | None:
    """
    Try to detect a person's name from:
    1. Document content — explicit "Name:", "Dear", "Mr./Dr." patterns
    2. Filename — consecutive Title Case words that aren't document keywords
    Returns a properly capitalised name string, or None if not found.
    """
    # ── 1. Scan document content (most reliable) ──────────────────────────
    text_sample = (raw_text or '')[:3000]
    for pattern in _NAME_FIELD_PATTERNS:
        m = re.search(pattern, text_sample, flags=re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            words = candidate.split()
            # All words must be plausible name parts (2–20 chars, not in blocklist)
            if all(2 <= len(w) <= 20 and w.lower() not in _NAME_BLOCKLIST for w in words):
                return ' '.join(w.capitalize() for w in words)

    # ── 2. Scan filename ───────────────────────────────────────────────────
    # Split filename (without extension) by _, -, space, digits
    stem = filename.rsplit('.', 1)[0] if '.' in filename else filename
    parts = re.split(r'[\s_\-]+', stem)
    # Collect parts that look like name words: 2-20 alpha chars, not in blocklist
    name_words = [
        p for p in parts
        if re.match(r'^[A-Za-z]{2,20}$', p) and p.lower() not in _NAME_BLOCKLIST
    ]
    if len(name_words) >= 2:
        # Use first two words as the full name (avoid trailing descriptors)
        return ' '.join(w.capitalize() for w in name_words[:2])

    return None


def _extract_name_hint(filename: str) -> str | None:
    """Return a short name hint from the filename for existing-folder matching."""
    stem = filename.rsplit('.', 1)[0] if '.' in filename else filename
    parts = re.split(r'[\s_\-]+', stem)
    for p in parts:
        if re.match(r'^[A-Za-z]{2,20}$', p) and p.lower() not in _NAME_BLOCKLIST:
            return p.capitalize()
    return None


def _match_existing_person_folder(user_id: int, candidate: str | None) -> str | None:
    """Prefer an existing person folder to avoid misrouting to legal/other buckets."""
    if not candidate:
        return None

    rows = (
        db.session.query(Document.user_folder)
        .filter_by(user_id=user_id, deleted_at=None)
        .filter(Document.user_folder.isnot(None))
        .distinct()
        .all()
    )
    if not rows:
        return None

    cand = candidate.strip().lower()
    for (folder,) in rows:
        if folder and folder.strip().lower() == cand:
            return folder

    # If we only have a first-name hint, match a longer existing folder
    if len(candidate.split()) == 1:
        for (folder,) in rows:
            if folder and folder.strip().lower().startswith(cand + ' '):
                return folder

    return None


def _match_existing_keyword_folder(user_id: int, filename: str, raw_text: str) -> str | None:
    """Match existing folder names against filename/content (Bitflow wins)."""
    combined = f"{filename} {raw_text or ''}".lower()
    if not combined.strip():
        return None

    combined_compact = re.sub(r'[^a-z0-9]+', '', combined)
    combined_tokens = set(re.findall(r'[a-z]{3,}', combined))

    rows = (
        db.session.query(Document.user_folder)
        .filter_by(user_id=user_id, deleted_at=None)
        .filter(Document.user_folder.isnot(None))
        .distinct()
        .all()
    )
    if not rows:
        return None

    # Bitflow wins when present
    if 'bitflow' in combined_compact:
        for (folder,) in rows:
            if folder and 'bitflow' in folder.lower():
                return folder

    # Prefer longer, more specific folder names
    for (folder,) in sorted(rows, key=lambda r: len(r[0] or ''), reverse=True):
        if not folder:
            continue
        folder_norm = re.sub(r'[^a-z0-9 ]+', ' ', folder.lower()).strip()
        if not folder_norm or folder_norm in _FOLDER_MATCH_STOP:
            continue

        # Exact phrase match
        if folder_norm in combined:
            return folder

        # Token match (ignore short/generic words)
        parts = [p for p in folder_norm.split() if len(p) >= 4 and p not in _FOLDER_MATCH_STOP]
        if parts and all(p in combined_tokens for p in parts):
            return folder

    return None


def _has_bitflow(filename: str, raw_text: str) -> bool:
    combined = f"{filename} {raw_text or ''}".lower()
    compact = re.sub(r'[^a-z0-9]+', '', combined)
    return 'bitflow' in compact


# ── LEGACY label (backward compat only — does NOT affect VirtualPaths) ────────
def _derive_folder_from_content(filename: str, raw_text: str, mime_type: str = '') -> str:
    """
    Smart folder derivation:
    1. Bitflow → Bitflow folder (highest priority)
    2. Images → Gallery subfolder derived from filename / context
    3. Documents → scan full text for specific phrases/keywords, first match wins
    4. Fallback → most frequent meaningful word from text
    5. Final fallback → 'General'
    """
    name_lower = filename.lower()
    ext = name_lower.rsplit('.', 1)[-1] if '.' in name_lower else ''
    text_lower = (raw_text or '').lower()
    name_no_ext = re.sub(r'[_\-\.]', ' ', name_lower.rsplit('.', 1)[0])
    combined = name_no_ext + ' ' + text_lower[:2000]

    # ── BITFLOW ─────────────────────────────────────────────────────────────
    if _has_bitflow(filename, raw_text):
        return 'Bitflow'

    # ── IMAGE FILES ──────────────────────────────────────────────────────────
    if ext in _IMAGE_EXTS or mime_type.startswith('image/'):
        for keywords, gallery_name in _GALLERY_CONTEXTS:
            for kw in keywords:
                if kw in combined:
                    return gallery_name
        return 'Gallery'

    # ── TEXT / DOCUMENT FILES ────────────────────────────────────────────────
    full_combined = name_no_ext + ' ' + text_lower[:5000]
    for keywords, folder in _DOC_RULES:
        for kw in keywords:
            if kw in full_combined:
                return folder

    # Frequency fallback
    all_words = re.findall(r'[a-z]{5,}', text_lower[:5000])
    freq = Counter(w for w in all_words if w not in _STOP_WORDS)
    if freq:
        return freq.most_common(1)[0][0].capitalize()

    return 'General'


def _run_upload_pipeline(tmp_path, original_filename, file_size, file_hash,
                         mime_type, user_id, tags_raw, manual_category, ip):
    """
    Core upload pipeline: extract → classify → store → persist.
    Called both from the sync path in upload_file() and from the async
    task queue (via task_queue.submit).  Must be called inside a Flask
    app context.

    Returns the same dict that upload_file() would return on success.
    """
    import tempfile as _tempfile
    from datetime import datetime as _dt
    from pathlib import Path as _Path

    storage = _get_storage()

    raw_text = ''
    extraction = {}
    try:
        extraction = TextExtractor.extract_text(tmp_path) or {}
        raw_text = extraction.get('text', '') if extraction.get('success') else ''
        if raw_text:
            raw_text = TextPreprocessor.preprocess(raw_text)
    except Exception as ext_err:
        logger.warning(f"Text extraction failed for {original_filename}: {ext_err}")

    entities = EntityExtractor.extract(raw_text)
    try:
        classifier = _get_classifier()
    except Exception:
        classifier = None

    attrs = AttributeExtractor.extract(
        filename=original_filename,
        raw_text=raw_text,
        entities=entities,
        classifier=classifier,
        user_id=user_id,
        db=db,
        manual_category=manual_category,
    )
    predicted_label  = attrs.doc_type
    confidence_score = attrs.confidence
    all_predictions  = attrs.all_predictions

    doc = Document(
        user_id=user_id,
        filename='',
        original_filename=original_filename,
        file_path='',
        file_size=file_size,
        file_hash=file_hash,
        mime_type=mime_type,
        predicted_label=predicted_label,
        confidence_score=confidence_score,
        suggested_folder=predicted_label,
        user_folder=predicted_label,
        doc_type=attrs.doc_type,
        client_name=attrs.client_name,
        doc_year=attrs.doc_year,
        entity_keywords=_format_entity_keywords(entities),
        extracted_text=raw_text[:10000] if raw_text else None,
        text_preview=raw_text[:500] if raw_text else None,
        tags=tags_raw or None,
        is_encrypted=True,
        is_duplicate=False,
        uploaded_at=_dt.utcnow(),
        processed_at=_dt.utcnow(),
    )
    db.session.add(doc)
    db.session.flush()

    store_result = storage.store_file_flat(tmp_path=tmp_path, user_id=user_id, file_id=doc.id)
    try:
        os.unlink(tmp_path)
    except OSError:
        pass

    if not store_result['success']:
        db.session.rollback()
        raise RuntimeError('File storage failed: ' + store_result.get('error', ''))

    doc.file_path = store_result['stored_path']
    doc.filename  = _Path(store_result['stored_path']).name

    meta = FileMetadata(
        document_id=doc.id,
        num_pages=extraction.get('num_pages'),
        word_count=len(raw_text.split()) if raw_text else 0,
        character_count=len(raw_text) if raw_text else 0,
        keywords=_format_entity_keywords(entities),
    )
    db.session.add(meta)

    try:
        from app.utils.path_generator import PathGenerator
        from app.models.virtual_path import HierarchyTemplate
        templates = HierarchyTemplate.query.filter_by(user_id=None).all()
        PathGenerator.generate_and_save(doc, templates, db)
    except Exception as vp_err:
        logger.warning(f"Virtual path generation failed for doc {doc.id}: {vp_err}")

    db.session.commit()
    _log_audit(user_id, 'upload', 'document', doc.id, 'success',
               f'Uploaded {original_filename}', ip)

    return {
        'success': True,
        'is_duplicate': False,
        'document_id': doc.id,
        'original_filename': original_filename,
        'predicted_label': predicted_label,
        'confidence_score': round(confidence_score, 4),
        'file_size': file_size,
        'tags': tags_raw or None,
        'all_predictions': all_predictions,
    }


# ============================================================
# POST /api/upload
# ============================================================

@upload_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """
    Upload, classify, encrypt and store a document.

    Multipart form fields:
        file (required) - the document file
        category (optional) - override AI category
        tags (optional) - comma-separated tags

    Returns JSON:
        {success, document_id, predicted_label, confidence_score,
         is_duplicate, original_filename, file_size}
    """
    user_id = int(get_jwt_identity())
    ip = request.remote_addr or '0.0.0.0'

    # ---- validate file presence ----
    if 'file' not in request.files:
        return {'success': False, 'error': 'No file part in request'}, 400

    file = request.files['file']
    if not file or file.filename == '':
        return {'success': False, 'error': 'No file selected'}, 400

    original_filename = secure_filename(file.filename)
    if not validate_filename(original_filename):
        return {'success': False, 'error': 'Invalid filename'}, 400

    if not _allowed_file(original_filename):
        allowed = ', '.join(current_app.config.get('ALLOWED_EXTENSIONS', set()))
        return {'success': False,
                'error': f'File type not allowed. Accepted: {allowed}'}, 415

    # ---- optional form fields ----
    manual_category = sanitize_input(request.form.get('category', '').strip())
    tags_raw = sanitize_input(request.form.get('tags', '').strip())

    try:
        storage = _get_storage()

        # ---- save to temp file for hashing & extraction ----
        suffix = Path(original_filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = tmp.name
            file.save(tmp_path)

        file_hash = storage.compute_hash(tmp_path)
        file_size = os.path.getsize(tmp_path)
        mime_type = mimetypes.guess_type(original_filename)[0] or 'application/octet-stream'

        # ---- duplicate detection ----
        existing = Document.query.filter_by(user_id=user_id, file_hash=file_hash, deleted_at=None).first()
        if existing:
            os.unlink(tmp_path)
            _log_audit(user_id, 'upload_duplicate', 'document',
                       existing.id, 'warning',
                       f'Duplicate of document {existing.id}', ip)
            return {
                'success': True,
                'is_duplicate': True,
                'message': f'"{existing.original_filename}" already exists in folder "{existing.user_folder or existing.predicted_label}".',
                'original_document_id': existing.id,
                'original_filename': existing.original_filename,
                'existing_folder': existing.user_folder or existing.predicted_label or 'General',
                'uploaded_at': existing.uploaded_at.isoformat() if existing.uploaded_at else None,
            }, 200

        # If a soft-deleted row has the same hash, release its hash so reupload works
        deleted_match = (
            Document.query
            .filter_by(user_id=user_id, file_hash=file_hash)
            .filter(Document.deleted_at.isnot(None))
            .first()
        )
        if deleted_match:
            try:
                _mutate_file_hash(deleted_match)
                db.session.commit()
            except Exception as mutate_err:
                db.session.rollback()
                logger.error(f"Mutate deleted hash error: {mutate_err}")
                return {'success': False, 'error': 'Duplicate cleanup failed'}, 500

        # ---- async fork: large files (>500 KB) or images go through task queue ----
        _ASYNC_SIZE_THRESHOLD = 500 * 1024  # 500 KB
        _ASYNC_MIME_PREFIXES = ('image/',)
        use_async = (
            file_size > _ASYNC_SIZE_THRESHOLD
            or any(mime_type.startswith(p) for p in _ASYNC_MIME_PREFIXES)
        )
        if use_async:
            from app.utils.task_queue import task_queue
            from flask import current_app
            app = current_app._get_current_object()

            def _async_upload(app, tmp_path, original_filename, file_size,
                              file_hash, mime_type, user_id, tags_raw,
                              manual_category, ip):
                with app.app_context():
                    return _run_upload_pipeline(
                        tmp_path=tmp_path,
                        original_filename=original_filename,
                        file_size=file_size,
                        file_hash=file_hash,
                        mime_type=mime_type,
                        user_id=user_id,
                        tags_raw=tags_raw,
                        manual_category=manual_category,
                        ip=ip,
                    )

            task_id = task_queue.submit(
                _async_upload, app, tmp_path, original_filename, file_size,
                file_hash, mime_type, user_id, tags_raw, manual_category, ip,
            )
            return {'success': True, 'async': True, 'task_id': task_id,
                    'message': 'File accepted for background processing'}, 202

        # ---- text extraction (never crash upload on failure) ----
        extraction = {}
        raw_text = ''
        processed_text = ''
        try:
            extraction = TextExtractor.extract_text(tmp_path) or {}
            raw_text = extraction.get('text', '') if extraction.get('success') else ''
            processed_text = TextPreprocessor.preprocess(raw_text) if raw_text else ''
        except Exception as ext_err:
            logger.warning(f"Text extraction failed for {original_filename}: {ext_err}")

        # ---- classification — attribute extraction (Phase 3 VFS) ----
        entities = EntityExtractor.extract(raw_text)
        try:
            classifier = _get_classifier()
        except Exception:
            classifier = None

        attrs = AttributeExtractor.extract(
            filename=original_filename,
            raw_text=raw_text,
            entities=entities,
            classifier=classifier,
            user_id=user_id,
            db=db,
            manual_category=manual_category,
        )
        predicted_label  = attrs.doc_type
        confidence_score = attrs.confidence
        all_predictions  = attrs.all_predictions

        # ---- persist Document first so we have doc.id for flat storage path ----
        doc = Document(
            user_id=user_id,
            filename='',           # filled in after flat store below
            original_filename=original_filename,
            file_path='',          # filled in after flat store below
            file_size=file_size,
            file_hash=file_hash,
            mime_type=mime_type,
            predicted_label=predicted_label,
            confidence_score=confidence_score,
            suggested_folder=predicted_label,
            user_folder=predicted_label,
            # Knowledge model attributes (Phase 3)
            doc_type=attrs.doc_type,
            client_name=attrs.client_name,
            doc_year=attrs.doc_year,
            entity_keywords=_format_entity_keywords(entities),
            extracted_text=raw_text[:10000] if raw_text else None,
            text_preview=raw_text[:500] if raw_text else None,
            tags=tags_raw or None,
            is_encrypted=True,
            is_duplicate=False,
            uploaded_at=datetime.utcnow(),
            processed_at=datetime.utcnow(),
        )
        db.session.add(doc)
        db.session.flush()  # assigns doc.id

        # ---- encrypt & store flat: uploads/{user_id}/storage/{doc.id}.enc ----
        store_result = storage.store_file_flat(
            tmp_path=tmp_path,
            user_id=user_id,
            file_id=doc.id,
        )
        os.unlink(tmp_path)  # always clean temp

        if not store_result['success']:
            db.session.rollback()
            return {'success': False,
                    'error': 'File storage failed: ' + store_result.get('error', '')}, 500

        # Back-fill the real path now that the file exists on disk
        doc.file_path = store_result['stored_path']
        doc.filename  = Path(store_result['stored_path']).name

        # ---- file metadata ----
        meta = FileMetadata(
            document_id=doc.id,
            num_pages=extraction.get('num_pages'),
            word_count=len(raw_text.split()) if raw_text else 0,
            character_count=len(raw_text) if raw_text else 0,
            keywords=_format_entity_keywords(entities),
        )
        db.session.add(meta)

        # ---- virtual paths (Phase 4 VFS) ----
        try:
            from app.utils.path_generator import PathGenerator
            from app.models.virtual_path import HierarchyTemplate
            templates = HierarchyTemplate.query.filter_by(user_id=None).all()
            PathGenerator.generate_and_save(doc, templates, db)
        except Exception as vp_err:
            logger.warning(f"Virtual path generation failed for doc {doc.id}: {vp_err}")

        db.session.commit()

        _log_audit(user_id, 'upload', 'document', doc.id, 'success',
                   f'Uploaded {original_filename}', ip)

        return {
            'success': True,
            'is_duplicate': False,
            'document_id': doc.id,
            'original_filename': original_filename,
            'predicted_label': predicted_label,
            'confidence_score': round(confidence_score, 4),
            'file_size': file_size,
            'tags': tags_raw or None,
            'all_predictions': all_predictions,
        }, 201

    except Exception as e:
        logger.error(f"Upload error: {e}")
        # Clean up temp file if it was created but not yet deleted
        try:
            if 'tmp_path' in dir() and os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except Exception:
            pass
        _log_audit(user_id, 'upload', 'document', None, 'error', str(e), ip)
        return {'success': False, 'error': f'Upload failed: {str(e)}'}, 500


# ============================================================
# GET /api/documents
# ============================================================

@upload_bp.route('/documents', methods=['GET'])
@jwt_required()
def list_documents():
    """
    List the current user's documents with optional filters.

    Query params:
        page (int, default 1)
        per_page (int, default 20, max 100)
        category (str) - filter by predicted_label
        search (str) - substring match on original_filename
    """
    user_id = int(get_jwt_identity())
    page     = max(1, request.args.get('page', 1, type=int))
    per_page = min(100, max(1, request.args.get('per_page', 20, type=int)))

    category_filter = sanitize_input(request.args.get('category', '').strip())
    doc_type_filter = sanitize_input(request.args.get('doc_type', '').strip())
    search_term     = sanitize_input(request.args.get('search', '').strip())
    sort_col        = request.args.get('sort', 'uploaded_at')
    sort_dir        = request.args.get('dir', 'desc')

    # Allowlist sortable columns to prevent SQL injection
    _SORTABLE = {
        'original_filename': Document.original_filename,
        'predicted_label':   Document.predicted_label,
        'confidence_score':  Document.confidence_score,
        'uploaded_at':       Document.uploaded_at,
        'file_size':         Document.file_size,
    }
    sort_attr = _SORTABLE.get(sort_col, Document.uploaded_at)
    order_expr = sort_attr.asc() if sort_dir == 'asc' else sort_attr.desc()

    try:
        query = Document.query.filter_by(user_id=user_id, deleted_at=None)

        if category_filter:
            query = query.filter(Document.predicted_label == category_filter)

        if doc_type_filter:
            query = query.filter(Document.doc_type == doc_type_filter)

        if search_term:
            query = query.filter(
                Document.original_filename.ilike(f'%{search_term}%')
            )

        query = query.order_by(order_expr)
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        documents = [d.to_dict() for d in paginated.items]

        return {
            'success': True,
            'documents': documents,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': paginated.total,
                'pages': paginated.pages,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev,
            }
        }, 200

    except Exception as e:
        logger.error(f"List documents error: {e}")
        return {'success': False, 'error': 'Could not retrieve documents'}, 500


# ============================================================
# GET /api/documents/<id>
# ============================================================

@upload_bp.route('/documents/<int:doc_id>', methods=['GET'])
@jwt_required()
def get_document(doc_id: int):
    """Get details of a single document (owned by current user)."""
    user_id = int(get_jwt_identity())

    doc = Document.query.filter_by(id=doc_id, user_id=user_id,
                                   deleted_at=None).first()
    if not doc:
        return {'success': False, 'error': 'Document not found'}, 404

    return {'success': True, 'document': doc.to_dict(include_content=True)}, 200


# ============================================================
# GET /api/documents/<id>/download
# ============================================================

@upload_bp.route('/documents/<int:doc_id>/download', methods=['GET'])
@jwt_required()
def download_document(doc_id: int):
    """Decrypt and stream a document back to the authenticated owner."""
    user_id = int(get_jwt_identity())
    ip = request.remote_addr or '0.0.0.0'

    doc = Document.query.filter_by(id=doc_id, user_id=user_id,
                                   deleted_at=None).first()
    if not doc:
        return {'success': False, 'error': 'Document not found'}, 404

    storage = _get_storage()
    plaintext = storage.get_decrypted_bytes(doc.file_path)

    if plaintext is None:
        return {'success': False, 'error': 'Could not decrypt file'}, 500

    _log_audit(user_id, 'download', 'document', doc.id, 'success',
               f'Downloaded {doc.original_filename}', ip)

    import io
    # ?inline=1 → render in browser (PDF/images); default → force download
    inline = request.args.get('inline', '0') == '1'
    return send_file(
        io.BytesIO(plaintext),
        download_name=doc.original_filename,
        mimetype=doc.mime_type or 'application/octet-stream',
        as_attachment=not inline,
    )


# ============================================================
# POST /api/documents/<id>/open  (local-only: opens with OS default app)
# ============================================================

@upload_bp.route('/documents/<int:doc_id>/open', methods=['POST'])
@jwt_required()
def open_document_native(doc_id: int):
    """Decrypt file to a previews folder and open with the OS default app."""
    user_id = int(get_jwt_identity())

    doc = Document.query.filter_by(id=doc_id, user_id=user_id,
                                   deleted_at=None).first()
    if not doc:
        return {'success': False, 'error': 'Document not found'}, 404

    storage = _get_storage()
    plaintext = storage.get_decrypted_bytes(doc.file_path)
    if plaintext is None:
        return {'success': False, 'error': 'Could not decrypt file'}, 500

    # Write decrypted bytes to data/previews/<original_filename>
    previews_dir = Path(current_app.root_path).parent / 'data' / 'previews'
    previews_dir.mkdir(parents=True, exist_ok=True)
    preview_path = previews_dir / secure_filename(doc.original_filename)
    preview_path.write_bytes(plaintext)

    # Open with the OS default application (Windows: os.startfile)
    try:
        os.startfile(str(preview_path.resolve()))
    except AttributeError:
        # Non-Windows fallback
        import subprocess
        subprocess.Popen(['xdg-open', str(preview_path.resolve())])

    _log_audit(user_id, 'open_native', 'document', doc.id, 'success',
               f'Opened {doc.original_filename}', request.remote_addr or '0.0.0.0')

    return {'success': True}, 200


# ============================================================
# PATCH /api/documents/<id>
# ============================================================

@upload_bp.route('/documents/<int:doc_id>', methods=['PATCH'])
@jwt_required()
def update_document(doc_id: int):
    """
    Update mutable document fields (category/folder and tags).

    JSON body (all optional):
        category (str) - reassign to new folder
        tags (str) - comma-separated tags
    """
    user_id = int(get_jwt_identity())
    ip = request.remote_addr or '0.0.0.0'

    doc = Document.query.filter_by(id=doc_id, user_id=user_id,
                                   deleted_at=None).first()
    if not doc:
        return {'success': False, 'error': 'Document not found'}, 404

    data = request.get_json() or {}

    try:
        if 'category' in data:
            new_category = sanitize_input(data['category'].strip())
            if new_category and new_category != doc.user_folder:
                storage = _get_storage()
                move_result = storage.move_file(doc.file_path, user_id, new_category)
                if move_result['success']:
                    doc.file_path = move_result['new_path']
                    doc.filename = Path(move_result['new_path']).name
                    doc.user_folder = new_category

        if 'tags' in data:
            doc.tags = sanitize_input(data['tags'].strip()) or None

        db.session.commit()
        _log_audit(user_id, 'update', 'document', doc.id, 'success',
                   'Updated document metadata', ip)
        return {'success': True, 'document': doc.to_dict()}, 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Update document error: {e}")
        return {'success': False, 'error': 'Update failed'}, 500


# ============================================================
# DELETE /api/documents/<id>
# ============================================================

@upload_bp.route('/documents/<int:doc_id>', methods=['DELETE'])
@jwt_required()
def delete_document(doc_id: int):
    """Soft-delete a document (marks deleted_at, optionally removes disk file)."""
    user_id = int(get_jwt_identity())
    ip = request.remote_addr or '0.0.0.0'

    doc = Document.query.filter_by(id=doc_id, user_id=user_id,
                                   deleted_at=None).first()
    if not doc:
        return {'success': False, 'error': 'Document not found'}, 404

    hard_delete = request.args.get('hard', 'false').lower() == 'true'

    try:
        # Always remove VirtualPath rows so Smart Views no longer show this doc
        from app.models.virtual_path import VirtualPath
        VirtualPath.query.filter_by(document_id=doc_id).delete()

        if hard_delete:
            storage = _get_storage()
            storage.delete_file(doc.file_path)
            db.session.delete(doc)
        else:
            doc.deleted_at = datetime.utcnow()
            _mutate_file_hash(doc)

        db.session.commit()
        _log_audit(user_id, 'delete', 'document', doc_id,
                   'success', f'{"Hard" if hard_delete else "Soft"} deleted', ip)
        return {'success': True, 'message': 'Document deleted'}, 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete document error: {e}")
        return {'success': False, 'error': 'Delete failed'}, 500


# ── POST /api/documents/bulk/delete ─────────────────────────────────────────
@upload_bp.route('/documents/bulk/delete', methods=['POST'])
@jwt_required()
def bulk_delete_documents():
    """
    Soft-delete multiple documents owned by the current user.

    JSON body:
        {"ids": [1, 2, 3]}

    Returns:
        {success, deleted, skipped}
    """
    from datetime import datetime
    from app.models.virtual_path import VirtualPath

    user_id = int(get_jwt_identity())
    ip = request.remote_addr or '0.0.0.0'
    data = request.get_json(silent=True) or {}
    ids = data.get('ids', [])

    if not isinstance(ids, list) or not ids:
        return {'success': False, 'error': 'ids must be a non-empty list'}, 400

    # Sanitise: only integers, cap at 500 per request
    try:
        ids = [int(i) for i in ids[:500]]
    except (TypeError, ValueError):
        return {'success': False, 'error': 'ids must be integers'}, 400

    deleted = 0
    skipped = 0

    try:
        docs = Document.query.filter(
            Document.id.in_(ids),
            Document.user_id == user_id,
            Document.deleted_at.is_(None),
        ).all()

        for doc in docs:
            doc.deleted_at = datetime.utcnow()
            VirtualPath.query.filter_by(document_id=doc.id).delete()
            deleted += 1

        skipped = len(ids) - deleted
        db.session.commit()
        _log_audit(user_id, 'bulk_delete', 'document', None, 'success',
                   f'Bulk deleted {deleted} docs', ip)
        return {'success': True, 'deleted': deleted, 'skipped': skipped}, 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Bulk delete error: {e}")
        return {'success': False, 'error': 'Bulk delete failed'}, 500


# ── POST /api/documents/<id>/reprocess ────────────────────────────────────────

@upload_bp.route('/documents/<int:doc_id>/reprocess', methods=['POST'])
@jwt_required()
def reprocess_document(doc_id: int):
    """
    Re-extract text, re-classify, and rebuild VirtualPaths for one document.

    Optional JSON body:
        {"force": true}   — rebuild even if attributes are unchanged

    Response:
        {success, doc_id, changes: {field: {old, new}}}
    """
    user_id = int(get_jwt_identity())

    doc = Document.query.filter_by(id=doc_id, user_id=user_id,
                                   deleted_at=None).first()
    if not doc:
        return {'success': False, 'error': 'Document not found'}, 404

    data = request.get_json(silent=True) or {}
    force = bool(data.get('force', False))

    from app.utils.reprocessor import Reprocessor
    result = Reprocessor.reprocess(doc_id, db, force=force)

    status = 200 if result.get('success') else 500
    return result, status


# ── POST /api/documents/reprocess-bulk ───────────────────────────────────────
@upload_bp.route('/documents/reprocess-bulk', methods=['POST'])
@jwt_required()
def reprocess_bulk():
    """
    Bulk-reprocess documents matching optional filters.

    JSON body (all optional):
        doc_type  (str)  — filter to a specific document type
        force     (bool) — pass force=True to Reprocessor

    Returns:
        JSON with counts: {queued, succeeded, failed, errors:[...]}
    """
    current_user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    doc_type_filter = data.get('doc_type')
    force = bool(data.get('force', False))

    from app.models.document import Document
    from app.utils.reprocessor import Reprocessor

    query = Document.query.filter_by(user_id=current_user_id, deleted_at=None)
    if doc_type_filter:
        query = query.filter_by(doc_type=doc_type_filter)

    docs = query.all()
    succeeded = 0
    failed = 0
    errors = []

    for doc in docs:
        result = Reprocessor.reprocess(doc.id, db, force=force)
        if result.get('success'):
            succeeded += 1
        else:
            failed += 1
            errors.append({'doc_id': doc.id, 'error': result.get('error', '')})

    return {
        'queued': len(docs),
        'succeeded': succeeded,
        'failed': failed,
        'errors': errors,
    }, 200


# ── GET /api/tasks/<task_id> ──────────────────────────────────────────────────
@upload_bp.route('/tasks/<task_id>', methods=['GET'])
@jwt_required()
def get_task_status(task_id: str):
    """
    Poll the status of an async background task (e.g. a large-file upload).

    Returns:
        200  {id, state: 'pending'|'running'|'done'|'error', result, error}
        404  if task_id is unknown
    """
    from app.utils.task_queue import task_queue
    status = task_queue.status(task_id)
    if status is None:
        return {'success': False, 'error': 'Task not found'}, 404
    return status, 200
