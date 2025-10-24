from flask import Blueprint, render_template
from config.database import db_manager

bp = Blueprint('side_projects', __name__, url_prefix='/side-projects')

@bp.route('/')
def index():
    """Side projects landing page"""
    return render_template('side-projects/index.html', page_title="Side Projects")

@bp.route('/tartan-design/')
def tartan_design():
    """Tartan Design Descriptions project homepage"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get tartan_designs_clan data
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'tartan_designs_clan' 
                ORDER BY ordinal_position
            """)
            headers = [row['column_name'] for row in cursor.fetchall()]
            
            cursor.execute("SELECT * FROM tartan_designs_clan ORDER BY id")
            tartan_data = cursor.fetchall()
            
            cursor.execute("SELECT COUNT(*) as count FROM tartan_designs_clan")
            total_count = cursor.fetchone()['count']
            
            # Get tartan_designs_register data
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'tartan_designs_register' 
                ORDER BY ordinal_position
            """)
            register_headers = [row['column_name'] for row in cursor.fetchall()]
            
            cursor.execute("SELECT * FROM tartan_designs_register ORDER BY id")
            register_data = cursor.fetchall()
            
            cursor.execute("SELECT COUNT(*) as count FROM tartan_designs_register")
            register_total_count = cursor.fetchone()['count']
            
        return render_template('side-projects/tartan-design/index.html', 
                             page_title="Tartan Design Descriptions",
                             headers=headers,
                             tartan_data=tartan_data,
                             total_count=total_count,
                             register_headers=register_headers,
                             register_data=register_data,
                             register_total_count=register_total_count)
    except Exception as e:
        # If database error, still render template but without data
        return render_template('side-projects/tartan-design/index.html', 
                             page_title="Tartan Design Descriptions",
                             headers=[],
                             tartan_data=None,
                             total_count=0,
                             register_headers=[],
                             register_data=None,
                             register_total_count=0,
                             error=str(e))

@bp.route('/<project_name>')
def project_detail(project_name):
    """Individual project page - placeholder for future projects"""
    return render_template('side-projects/project.html', 
                         project_name=project_name,
                         page_title=f"{project_name.title()} - Side Projects")
