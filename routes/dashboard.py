from flask import Blueprint, render_template

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def dashboard():
    """
    Main dashboard view. Renders the base template.
    All dynamic data is loaded asynchronously via JavaScript and API calls.
    """
    return render_template('dashboard.html')
