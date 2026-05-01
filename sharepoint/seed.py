"""Seed the database with sample data for demonstration."""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from datetime import date, datetime, timezone
from app import create_app
from models import db
from models.user import User
from models.binder import Binder, BinderAccess, Folder
from models.document import Document, DocumentVersion


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        # Check if already seeded
        if User.query.filter_by(username='admin').first():
            print('Database already seeded.')
            return

        # Create users
        admin = User(username='admin', email='admin@firm.com', full_name='Admin User', role='admin')
        admin.set_password('admin')

        manager = User(username='jsmith', email='jsmith@firm.com', full_name='John Smith', role='manager')
        manager.set_password('password')

        staff1 = User(username='mjones', email='mjones@firm.com', full_name='Mary Jones', role='staff')
        staff1.set_password('password')

        staff2 = User(username='bwilson', email='bwilson@firm.com', full_name='Bob Wilson', role='staff')
        staff2.set_password('password')

        db.session.add_all([admin, manager, staff1, staff2])
        db.session.flush()

        # Create sample binder: Acme Corp Audit
        binder1 = Binder(
            name='Acme Corp - 2025 Audit',
            client_name='Acme Corporation',
            engagement_type='audit',
            description='Annual financial statement audit for Acme Corporation.',
            period_end_date=date(2025, 12, 31),
            created_by=admin.id
        )
        db.session.add(binder1)
        db.session.flush()

        # Access for all users
        for user, level in [(admin, 'owner'), (manager, 'editor'), (staff1, 'editor'), (staff2, 'viewer')]:
            db.session.add(BinderAccess(binder_id=binder1.id, user_id=user.id, access_level=level))

        # Folders
        f_planning = Folder(binder_id=binder1.id, name='Planning', index_number='A', sort_order=1)
        f_testing = Folder(binder_id=binder1.id, name='Testing', index_number='B', sort_order=2)
        f_completion = Folder(binder_id=binder1.id, name='Completion', index_number='C', sort_order=3)
        f_financial = Folder(binder_id=binder1.id, name='Financial Statements', index_number='D', sort_order=4)
        db.session.add_all([f_planning, f_testing, f_completion, f_financial])
        db.session.flush()

        # Sub-folders
        f_risk = Folder(binder_id=binder1.id, parent_id=f_planning.id, name='Risk Assessment', index_number='A-1', sort_order=1)
        f_materiality = Folder(binder_id=binder1.id, parent_id=f_planning.id, name='Materiality', index_number='A-2', sort_order=2)
        f_revenue = Folder(binder_id=binder1.id, parent_id=f_testing.id, name='Revenue Testing', index_number='B-1', sort_order=1)
        f_expenses = Folder(binder_id=binder1.id, parent_id=f_testing.id, name='Expense Testing', index_number='B-2', sort_order=2)
        db.session.add_all([f_risk, f_materiality, f_revenue, f_expenses])
        db.session.flush()

        # Create placeholder documents (no actual files, just DB records for demo)
        sample_docs = [
            (f_planning.id, 'Engagement Letter.pdf', 'pdf', admin.id),
            (f_planning.id, 'Audit Plan.docx', 'docx', manager.id),
            (f_risk.id, 'Risk Assessment Workpaper.xlsx', 'xlsx', staff1.id),
            (f_materiality.id, 'Materiality Calculation.xlsx', 'xlsx', staff1.id),
            (f_revenue.id, 'Revenue Detail Testing.xlsx', 'xlsx', staff1.id),
            (f_revenue.id, 'Revenue Cutoff Memo.docx', 'docx', manager.id),
            (f_expenses.id, 'Expense Vouching.xlsx', 'xlsx', staff2.id),
            (f_completion.id, 'Management Letter.docx', 'docx', manager.id),
            (f_completion.id, 'Going Concern Memo.pdf', 'pdf', admin.id),
            (f_financial.id, 'Draft Financial Statements.pdf', 'pdf', admin.id),
            (f_financial.id, 'Trial Balance.xlsx', 'xlsx', staff1.id),
        ]

        for folder_id, name, ftype, user_id in sample_docs:
            doc = Document(
                folder_id=folder_id, binder_id=binder1.id,
                name=name, file_type=ftype, created_by=user_id
            )
            db.session.add(doc)
            db.session.flush()

            # Create a dummy version entry (no actual file on disk)
            ver = DocumentVersion(
                document_id=doc.id, version_number=1,
                file_path=f'placeholder_{doc.id}.{ftype}',
                file_size=1024 * (doc.id + 1),
                uploaded_by=user_id, comment='Initial upload'
            )
            db.session.add(ver)

        # Create second binder: Beta LLC Tax
        binder2 = Binder(
            name='Beta LLC - 2025 Tax Return',
            client_name='Beta LLC',
            engagement_type='tax',
            description='Annual tax return preparation.',
            period_end_date=date(2025, 12, 31),
            created_by=manager.id
        )
        db.session.add(binder2)
        db.session.flush()

        db.session.add(BinderAccess(binder_id=binder2.id, user_id=manager.id, access_level='owner'))
        db.session.add(BinderAccess(binder_id=binder2.id, user_id=staff1.id, access_level='editor'))

        for idx, name, order in [('1', 'Tax Organizer', 1), ('2', 'Workpapers', 2), ('3', 'Returns', 3)]:
            db.session.add(Folder(binder_id=binder2.id, name=name, index_number=idx, sort_order=order))

        # Create third binder: Gamma Review
        binder3 = Binder(
            name='Gamma Inc - Q4 2025 Review',
            client_name='Gamma Inc',
            engagement_type='review',
            description='Quarterly review engagement.',
            period_end_date=date(2025, 12, 31),
            created_by=admin.id
        )
        db.session.add(binder3)
        db.session.flush()
        db.session.add(BinderAccess(binder_id=binder3.id, user_id=admin.id, access_level='owner'))

        for idx, name, order in [('A', 'Planning', 1), ('B', 'Analytical Procedures', 2), ('C', 'Reporting', 3)]:
            db.session.add(Folder(binder_id=binder3.id, name=name, index_number=idx, sort_order=order))

        db.session.commit()
        print('Database seeded successfully!')
        print()
        print('Sample users:')
        print('  admin / admin      (Admin)')
        print('  jsmith / password   (Manager)')
        print('  mjones / password   (Staff)')
        print('  bwilson / password  (Staff)')


if __name__ == '__main__':
    seed()
