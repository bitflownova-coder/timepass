"""
Virtual Path Models - Multi-dimensional virtual file system (Phase 1)

VirtualPath   : One row per (document × view).  Same file may have 3+ rows,
                one for by_type, one for by_client, one for by_time, etc.
HierarchyTemplate : Defines how a view is built from document attributes.
"""
from datetime import datetime
from app.models.user import db


class HierarchyTemplate(db.Model):
    """
    Defines a named view and how its 3 levels map to document attributes.

    Seeded defaults:
        by_type   : level1=doc_type   / level2=client_name / level3=doc_year
        by_client : level1=client_name / level2=doc_type   / level3=doc_year
        by_time   : level1=doc_year   / level2=doc_type    / level3=client_name

    user_id=None means system-wide default; per-user overrides have a user_id.
    """
    __tablename__ = 'hierarchy_template'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    view_name = db.Column(db.String(64), nullable=False)       # e.g. 'by_type'
    display_name = db.Column(db.String(100), nullable=False)   # e.g. 'By Type'
    level1_attr = db.Column(db.String(50), nullable=False)     # attribute name on Document
    level2_attr = db.Column(db.String(50), nullable=False)
    level3_attr = db.Column(db.String(50), nullable=True)      # optional 3rd level
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'view_name': self.view_name,
            'display_name': self.display_name,
            'level1_attr': self.level1_attr,
            'level2_attr': self.level2_attr,
            'level3_attr': self.level3_attr,
        }

    def __repr__(self):
        return f'<HierarchyTemplate {self.view_name}>'


class VirtualPath(db.Model):
    """
    One row per (document × view).

    path  : full slash-joined string, e.g. 'Invoices/ABC Corp/2024'
    level1/2/3 : individual segments — used for GROUP BY in tree queries
    """
    __tablename__ = 'virtual_path'

    __table_args__ = (
        db.UniqueConstraint(
            'document_id', 'view_name',
            name='uq_virtual_path_doc_view',
        ),
        db.UniqueConstraint(
            'indexed_file_id', 'view_name',
            name='uq_virtual_path_indexed_view',
        ),
        db.Index('ix_virtual_path_user_view', 'user_id', 'view_name'),
        db.Index('ix_virtual_path_user_view_l1', 'user_id', 'view_name', 'level1'),
        db.Index('ix_virtual_path_user_view_l1_l2', 'user_id', 'view_name', 'level1', 'level2'),
        db.Index('ix_virtual_path_indexed_file', 'indexed_file_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    # Either document_id OR indexed_file_id is set (mutually exclusive)
    document_id = db.Column(
        db.Integer, db.ForeignKey('document.id', ondelete='CASCADE'),
        nullable=True, index=True,
    )
    indexed_file_id = db.Column(
        db.Integer, db.ForeignKey('indexed_file.id', ondelete='CASCADE'),
        nullable=True, index=True,
    )
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    view_name = db.Column(db.String(64), nullable=False)   # 'by_type' | 'by_client' | 'by_time' | 'code_projects'
    path = db.Column(db.String(760), nullable=False)       # 'Invoices/ABC Corp/2024'
    level1 = db.Column(db.String(255), nullable=False)
    level2 = db.Column(db.String(255), nullable=True)
    level3 = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationship back to Document
    document = db.relationship('Document', backref=db.backref('virtual_paths', lazy='dynamic', cascade='all, delete-orphan'))
    indexed_file = db.relationship('IndexedFile', backref=db.backref('virtual_paths', lazy='dynamic', cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'indexed_file_id': self.indexed_file_id,
            'view_name': self.view_name,
            'path': self.path,
            'level1': self.level1,
            'level2': self.level2,
            'level3': self.level3,
        }

    def __repr__(self):
        return f'<VirtualPath doc={self.document_id} view={self.view_name} path={self.path!r}>'


# ---------------------------------------------------------------------------
# Default hierarchy templates (seeded once on first app start)
# ---------------------------------------------------------------------------
DEFAULT_TEMPLATES = [
    {
        'view_name': 'by_type',
        'display_name': 'By Type',
        'level1_attr': 'doc_type',
        'level2_attr': 'client_name',
        'level3_attr': 'doc_year',
    },
    {
        'view_name': 'by_client',
        'display_name': 'By Client',
        'level1_attr': 'client_name',
        'level2_attr': 'doc_type',
        'level3_attr': 'doc_year',
    },
    {
        'view_name': 'by_time',
        'display_name': 'By Time',
        'level1_attr': 'doc_year',
        'level2_attr': 'doc_type',
        'level3_attr': 'client_name',
    },
    {
        'view_name': 'code_projects',
        'display_name': 'Code Projects',
        'level1_attr': 'project_name',
        'level2_attr': 'language',
        'level3_attr': None,
    },
]


def seed_hierarchy_templates():
    """Insert default HierarchyTemplate rows if they don't exist yet."""
    for tpl in DEFAULT_TEMPLATES:
        exists = HierarchyTemplate.query.filter_by(
            view_name=tpl['view_name'], user_id=None
        ).first()
        if not exists:
            db.session.add(HierarchyTemplate(user_id=None, **tpl))
    db.session.commit()
