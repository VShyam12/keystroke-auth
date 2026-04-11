from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import datetime
import warnings


bank_bp = Blueprint('bank_bp', __name__)


def _utcnow_isoformat():
    """Return current UTC time in ISO format while suppressing utcnow deprecation warnings."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        now_utc = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    return now_utc.isoformat()


@bank_bp.route('/account', methods=['GET'])
@jwt_required()
def get_account():
    """Return account details for the authenticated user."""
    user_id = get_jwt_identity()

    return jsonify({
        'user_id': user_id,
        'account_number': 'XXXX XXXX 4829',
        'account_type': 'Primary Savings Account',
        'balance': 245830.00,
        'available_balance': 245830.00,
        'currency': 'INR',
        'status': 'ACTIVE',
        'holder_name': 'Shyam Venkat',
        'ifsc': 'SECB0001234',
        'branch': 'Bengaluru Main Branch'
    }), 200


@bank_bp.route('/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    """Return the latest transactions and summary totals for the authenticated user."""
    _ = get_jwt_identity()

    transactions = [
        {
            'id': 1,
            'date': 'Apr 10',
            'description': 'Netflix Subscription',
            'category': 'Entertainment',
            'amount': -649,
            'type': 'debit',
            'status': 'Completed'
        },
        {
            'id': 2,
            'date': 'Apr 9',
            'description': 'Salary Credit',
            'category': 'Income',
            'amount': 85000,
            'type': 'credit',
            'status': 'Completed'
        },
        {
            'id': 3,
            'date': 'Apr 8',
            'description': 'Amazon Purchase',
            'category': 'Shopping',
            'amount': -2340,
            'type': 'debit',
            'status': 'Completed'
        },
        {
            'id': 4,
            'date': 'Apr 7',
            'description': 'Electricity Bill',
            'category': 'Utilities',
            'amount': -1820,
            'type': 'debit',
            'status': 'Completed'
        },
        {
            'id': 5,
            'date': 'Apr 6',
            'description': 'Interest Credit',
            'category': 'Income',
            'amount': 312,
            'type': 'credit',
            'status': 'Completed'
        },
        {
            'id': 6,
            'date': 'Apr 5',
            'description': 'Grocery Store',
            'category': 'Food',
            'amount': -1450,
            'type': 'debit',
            'status': 'Completed'
        },
        {
            'id': 7,
            'date': 'Apr 4',
            'description': 'Gym Membership',
            'category': 'Health',
            'amount': -2500,
            'type': 'debit',
            'status': 'Completed'
        },
        {
            'id': 8,
            'date': 'Apr 3',
            'description': 'Freelance Payment',
            'category': 'Income',
            'amount': 15000,
            'type': 'credit',
            'status': 'Completed'
        },
        {
            'id': 9,
            'date': 'Apr 2',
            'description': 'Restaurant',
            'category': 'Food',
            'amount': -890,
            'type': 'debit',
            'status': 'Completed'
        },
        {
            'id': 10,
            'date': 'Apr 1',
            'description': 'Mobile Recharge',
            'category': 'Utilities',
            'amount': -599,
            'type': 'debit',
            'status': 'Completed'
        }
    ]

    return jsonify({
        'transactions': transactions,
        'total': 10,
        'total_credits': 100312,
        'total_debits': 9608
    }), 200


@bank_bp.route('/transfer', methods=['POST'])
@jwt_required()
def transfer_funds():
    """Validate and record a transfer initiation request for the authenticated user."""
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}

    recipient_name = payload.get('recipient_name')
    _ = payload.get('recipient_account')
    _ = payload.get('bank_name')
    amount = payload.get('amount')
    _ = payload.get('note')
    _ = payload.get('transfer_type')

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': 'Amount must be greater than zero'}), 400

    if amount <= 0:
        return jsonify({'status': 'error', 'message': 'Amount must be greater than zero'}), 400

    with warnings.catch_warnings():
        warnings.simplefilter('ignore', DeprecationWarning)
        txn_suffix = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')

    return jsonify({
        'status': 'success',
        'message': 'Transfer initiated successfully',
        'transaction_id': 'TXN' + str(user_id) + txn_suffix,
        'amount': amount,
        'recipient': recipient_name,
        'timestamp': _utcnow_isoformat()
    }), 200


@bank_bp.route('/documents', methods=['GET'])
@jwt_required()
def list_documents():
    """Return available banking documents for download."""
    documents = [
        {'id': 1, 'name': 'March 2026 Statement', 'type': 'Statements', 'size': '245 KB', 'date': '2026-03-31'},
        {'id': 2, 'name': 'February 2026 Statement', 'type': 'Statements', 'size': '198 KB', 'date': '2026-02-28'},
        {'id': 3, 'name': 'January 2026 Statement', 'type': 'Statements', 'size': '312 KB', 'date': '2026-01-31'},
        {'id': 4, 'name': 'December 2025 Statement', 'type': 'Statements', 'size': '287 KB', 'date': '2025-12-31'},
        {'id': 5, 'name': 'November 2025 Statement', 'type': 'Statements', 'size': '203 KB', 'date': '2025-11-30'},
        {'id': 6, 'name': 'October 2025 Statement', 'type': 'Statements', 'size': '176 KB', 'date': '2025-10-31'},
        {'id': 7, 'name': 'Form 26AS - FY 2025-26', 'type': 'Tax Documents', 'size': '1.2 MB', 'date': '2026-04-01'},
        {'id': 8, 'name': 'Interest Certificate FY25', 'type': 'Tax Documents', 'size': '89 KB', 'date': '2026-04-01'},
        {'id': 9, 'name': 'TDS Certificate Q4', 'type': 'Tax Documents', 'size': '124 KB', 'date': '2026-03-31'},
        {'id': 10, 'name': 'Annual Account Summary', 'type': 'Reports', 'size': '892 KB', 'date': '2026-04-01'},
        {'id': 11, 'name': 'Portfolio Analysis Report', 'type': 'Reports', 'size': '445 KB', 'date': '2026-03-15'},
        {'id': 12, 'name': 'Transaction Analytics', 'type': 'Reports', 'size': '334 KB', 'date': '2026-03-01'}
    ]

    current_date = datetime.datetime.now(datetime.timezone.utc).date()
    for doc in documents:
        doc_date = datetime.datetime.strptime(doc['date'], '%Y-%m-%d').date()
        doc['is_new'] = (current_date - doc_date).days <= 30

    return jsonify({'documents': documents, 'total': 12}), 200


@bank_bp.route('/documents/download', methods=['POST'])
@jwt_required()
def download_document():
    """Log a document download request for the authenticated session."""
    payload = request.get_json(silent=True) or {}
    document_name = payload.get('document_name')

    if not document_name:
        return jsonify({'status': 'error', 'message': 'document_name is required'}), 400

    return jsonify({
        'status': 'success',
        'message': 'Download logged',
        'document': document_name
    }), 200
