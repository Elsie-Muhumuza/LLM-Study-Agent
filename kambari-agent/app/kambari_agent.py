import os
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from app.db import get_db_connection, init_db
from app.question_generator import generate_study_guide, save_study_guide
from app.roles_engine import assign_roles, get_role_assignments, update_role_assignment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path(__file__).parent.parent / 'data'
DB_PATH = Path(__file__).parent.parent / 'kambari.db'
THEME_FILES = {
    'parables': DATA_DIR / 'parables.json',
    'miracles': DATA_DIR / 'miracles.json',
    'teachings': DATA_DIR / 'teachings.json',
    'psalms': DATA_DIR / 'psalms.json',
    'proverbs': DATA_DIR / 'proverbs.json',
}

class KambariAgent:
    """Main class for the Kambari Altar Agent."""
    
    def __init__(self):
        """Initialize the Kambari Agent."""
        self.db_path = DB_PATH
        self.data_dir = DATA_DIR
        self.theme_files = THEME_FILES
        self._ensure_data_dir()
        self._init_db()
    
    def _ensure_data_dir(self):
        """Ensure the data directory exists."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create default theme files if they don't exist
        default_themes = {
            'parables.json': [
                {"title": "The Good Samaritan", "reference": "Luke 10:25-37"},
                {"title": "The Prodigal Son", "reference": "Luke 15:11-32"}
            ],
            'miracles.json': [
                {"title": "Jesus Feeds the 5000", "reference": "John 6:1-15"},
                {"title": "Jesus Walks on Water", "reference": "Matthew 14:22-33"}
            ],
            'teachings.json': [
                {"title": "The Beatitudes", "reference": "Matthew 5:1-12"},
                {"title": "The Lord's Prayer", "reference": "Matthew 6:9-13"}
            ]
        }
        
        for filename, content in default_themes.items():
            filepath = self.data_dir / filename
            if not filepath.exists():
                with open(filepath, 'w') as f:
                    json.dump(content, f, indent=2)
    
    def _init_db(self):
        """Initialize the database if it doesn't exist."""
        if not self.db_path.exists():
            init_db()
            logger.info("Initialized new database at %s", self.db_path)
    
    def create_series(self, title: str, theme: str, start_date: str, 
                     weeks: int = 4) -> int:
        """
        Create a new Bible study series.
        
        Args:
            title: Title of the series
            theme: Theme of the series (e.g., 'parables', 'miracles')
            start_date: Start date in 'YYYY-MM-DD' format
            weeks: Number of weeks for the series
            
        Returns:
            int: ID of the created series
        """
        theme_file = self.theme_files.get(theme.lower())
        if not theme_file or not theme_file.exists():
            raise ValueError(f"Invalid theme or theme file not found: {theme}")
        
        # Load passages from theme file
        with open(theme_file, 'r') as f:
            passages = json.load(f)
        
        if len(passages) < weeks:
            raise ValueError(f"Not enough passages in theme. Need {weeks}, found {len(passages)}")
        
        conn = get_db_connection()
        try:
            # Create the series
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO series (title, theme, start_date) VALUES (?, ?, ?)',
                (title, theme, start_date)
            )
            series_id = cursor.lastrowid
            
            # Add passages to the series
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            for i in range(weeks):
                passage = passages[i % len(passages)]  # Loop if not enough passages
                session_date = start_date + timedelta(weeks=i)
                
                cursor.execute(
                    '''INSERT INTO passages 
                       (series_id, title, reference, session_date)
                       VALUES (?, ?, ?, ?)''',
                    (series_id, passage['title'], passage['reference'], session_date.isoformat())
                )
            
            conn.commit()
            logger.info("Created new series '%s' with %d sessions", title, weeks)
            return series_id
            
        except Exception as e:
            conn.rollback()
            logger.error("Error creating series: %s", str(e))
            raise
        finally:
            conn.close()
    
    def generate_materials(self, series_id: int, output_dir: str = None) -> List[Dict]:
        """
        Generate study materials for all passages in a series.
        
        Args:
            series_id: ID of the series
            output_dir: Directory to save generated materials (default: data/study_guides)
            
        Returns:
            List of dictionaries containing generated materials
        """
        if output_dir is None:
            output_dir = self.data_dir / 'study_guides'
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        conn = get_db_connection()
        try:
            # Get series and passages
            series = conn.execute(
                'SELECT * FROM series WHERE id = ?', (series_id,)
            ).fetchone()
            
            if not series:
                raise ValueError(f"Series with ID {series_id} not found")
            
            passages = conn.execute(
                'SELECT * FROM passages WHERE series_id = ? ORDER BY session_date',
                (series_id,)
            ).fetchall()
            
            if not passages:
                raise ValueError(f"No passages found for series ID {series_id}")
            
            # Generate materials for each passage
            results = []
            for passage in passages:
                # Check if materials already exist
                existing = conn.execute(
                    'SELECT id FROM generated_materials WHERE passage_id = ?',
                    (passage['id'],)
                ).fetchone()
                
                if existing:
                    logger.info("Materials already exist for %s - %s", 
                               passage['title'], passage['reference'])
                    continue
                
                # Generate study guide
                logger.info("Generating materials for %s - %s", 
                           passage['title'], passage['reference'])
                
                study_guide = generate_study_guide(
                    passage_reference=passage['reference'],
                    theme=series['theme']
                )
                
                # Save to database
                cursor = conn.cursor()
                cursor.execute(
                    '''INSERT INTO generated_materials 
                       (passage_id, questions, discussion_points, prayer_points)
                       VALUES (?, ?, ?, ?)''',
                    (
                        passage['id'],
                        json.dumps(study_guide['discussion']),
                        json.dumps(study_guide['discussion']),
                        json.dumps(study_guide['reflection'])
                    )
                )
                
                # Save to file
                filepath = save_study_guide(
                    study_guide,
                    output_dir=str(output_dir)
                )
                
                results.append({
                    'passage_id': passage['id'],
                    'title': passage['title'],
                    'reference': passage['reference'],
                    'filepath': filepath
                })
            
            conn.commit()
            return results
            
        except Exception as e:
            conn.rollback()
            logger.error("Error generating materials: %s", str(e))
            raise
        finally:
            conn.close()
    
    def schedule_roles(self, start_date: str = None, weeks: int = 4) -> List[Dict]:
        """
        Schedule roles for upcoming study sessions.
        
        Args:
            start_date: Start date in 'YYYY-MM-DD' format (default: next Thursday)
            weeks: Number of weeks to schedule
            
        Returns:
            List of scheduled role assignments
        """
        if not start_date:
            today = datetime.now().date()
            days_until_thursday = (3 - today.weekday()) % 7
            if days_until_thursday == 0:  # If today is Thursday
                days_until_thursday = 7
            start_date = (today + timedelta(days=days_until_thursday)).isoformat()
        
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        results = []
        
        for week in range(weeks):
            session_date = start_date + timedelta(weeks=week)
            try:
                assignments = assign_roles(session_date.isoformat())
                results.append({
                    'date': session_date.isoformat(),
                    'assignments': assignments
                })
                logger.info("Scheduled roles for %s", session_date)
            except Exception as e:
                logger.error("Error scheduling roles for %s: %s", 
                            session_date, str(e))
        
        return results
    
    def get_upcoming_schedule(self, days_ahead: int = 30) -> List[Dict]:
        """
        Get the schedule of upcoming study sessions and role assignments.
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of scheduled sessions with role assignments
        """
        conn = get_db_connection()
        try:
            cursor = conn.execute('''
                SELECT 
                    p.session_date,
                    s.title as series_title,
                    p.title as passage_title,
                    p.reference,
                    json_group_array(
                        json_object(
                            'role', sch.role,
                            'member_id', m.id,
                            'member_name', m.name
                        )
                    ) as role_assignments
                FROM passages p
                JOIN series s ON p.series_id = s.id
                LEFT JOIN schedule sch ON sch.session_date = p.session_date
                LEFT JOIN members m ON sch.member_id = m.id
                WHERE p.session_date >= date('now')
                AND p.session_date <= date('now', ? || ' days')
                GROUP BY p.id
                ORDER BY p.session_date
            ''', (str(days_ahead),))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result['role_assignments'] = json.loads(result['role_assignments'])
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error("Error fetching upcoming schedule: %s", str(e))
            raise
        finally:
            conn.close()

def run_streamlit_app():
    """Run the Streamlit web interface."""
    import streamlit as st
    from datetime import date, timedelta
    
    st.set_page_config(
        page_title="Kambari Altar Agent",
        page_icon="✝️",
        layout="wide"
    )
    
    st.title("✝️ Kambari Altar Agent")
    
    # Initialize the agent
    agent = KambariAgent()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Dashboard", "Series", "Members", "Schedule", "Generate Materials"]
    )
    
    if page == "Dashboard":
        st.header("📊 Dashboard")
        
        # Upcoming sessions
        st.subheader("Upcoming Study Sessions")
        upcoming = agent.get_upcoming_schedule(days_ahead=30)
        
        if not upcoming:
            st.info("No upcoming study sessions scheduled.")
        else:
            for session in upcoming:
                with st.expander(f"{session['session_date']} - {session['series_title']}"):
                    st.write(f"**Passage:** {session['passage_title']} ({session['reference']})")
                    
                    # Display role assignments
                    st.write("**Role Assignments:**")
                    for assignment in session['role_assignments']:
                        if assignment['member_name']:
                            st.write(f"- {assignment['role'].title().replace('_', ' ')}: {assignment['member_name']}")
    
    elif page == "Series":
        st.header("📚 Study Series")
        
        # Create new series
        with st.expander("➕ Create New Series", expanded=False):
            with st.form("create_series"):
                title = st.text_input("Series Title")
                theme = st.selectbox(
                    "Theme",
                    ["Parables", "Miracles", "Teachings", "Psalms", "Proverbs"]
                )
                start_date = st.date_input("Start Date", date.today())
                weeks = st.number_input("Number of Weeks", min_value=1, max_value=52, value=4)
                
                if st.form_submit_button("Create Series"):
                    try:
                        series_id = agent.create_series(
                            title=title,
                            theme=theme.lower(),
                            start_date=start_date.isoformat(),
                            weeks=weeks
                        )
                        st.success(f"Created series '{title}' with ID {series_id}")
                    except Exception as e:
                        st.error(f"Error creating series: {str(e)}")
        
        # List existing series
        st.subheader("Existing Series")
        conn = get_db_connection()
        series_list = conn.execute('SELECT * FROM series ORDER BY start_date DESC').fetchall()
        
        if not series_list:
            st.info("No study series found.")
        else:
            for series in series_list:
                with st.expander(f"{series['title']} ({series['theme']})"):
                    st.write(f"**Start Date:** {series['start_date']}")
                    st.write(f"**Status:** {'Active' if series['is_active'] else 'Inactive'}")
                    
                    # Show passages in this series
                    passages = conn.execute(
                        'SELECT * FROM passages WHERE series_id = ? ORDER BY session_date',
                        (series['id'],)
                    ).fetchall()
                    
                    st.write(f"**Passages ({len(passages)}):**")
                    for passage in passages:
                        st.write(f"- {passage['title']} ({passage['reference']}) - {passage['session_date']}")
        
        conn.close()
    
    elif page == "Members":
        st.header("👥 Members")
        
        # Add new member
        with st.expander("➕ Add New Member", expanded=False):
            with st.form("add_member"):
                name = st.text_input("Full Name")
                phone = st.text_input("Phone Number")
                email = st.text_input("Email (optional)")
                
                if st.form_submit_button("Add Member"):
                    try:
                        from .db import add_member
                        member_id = add_member(name=name, phone=phone, email=email)
                        st.success(f"Added member: {name} (ID: {member_id})")
                    except Exception as e:
                        st.error(f"Error adding member: {str(e)}")
        
        # List members
        st.subheader("All Members")
        conn = get_db_connection()
        members = conn.execute('SELECT * FROM members ORDER BY name').fetchall()
        
        if not members:
            st.info("No members found. Add some members to get started!")
        else:
            for member in members:
                with st.expander(f"{member['name']}"):
                    st.write(f"**Phone:** {member['phone']}")
                    if member['email']:
                        st.write(f"**Email:** {member['email']}")
                    st.write(f"**Status:** {'Active' if member['is_active'] else 'Inactive'}")
                    
                    # Show upcoming roles
                    upcoming_roles = conn.execute('''
                        SELECT s.session_date, s.role 
                        FROM schedule s
                        WHERE s.member_id = ?
                        AND s.session_date >= date('now')
                        ORDER BY s.session_date
                    ''', (member['id'],)).fetchall()
                    
                    if upcoming_roles:
                        st.write("**Upcoming Roles:**")
                        for role in upcoming_roles:
                            st.write(f"- {role['role'].replace('_', ' ').title()} on {role['session_date']}")
        
        conn.close()
    
    elif page == "Schedule":
        st.header("📅 Schedule")
        
        # Schedule roles for upcoming sessions
        st.subheader("Schedule Roles")
        with st.form("schedule_roles"):
            start_date = st.date_input("Start Date", 
                                     value=date.today() + timedelta(days=(3 - date.today().weekday()) % 7))
            weeks = st.number_input("Number of Weeks", min_value=1, max_value=12, value=4)
            
            if st.form_submit_button("Schedule Roles"):
                with st.spinner("Scheduling roles..."):
                    try:
                        results = agent.schedule_roles(
                            start_date=start_date.isoformat(),
                            weeks=weeks
                        )
                        st.success(f"Scheduled roles for {len(results)} sessions")
                    except Exception as e:
                        st.error(f"Error scheduling roles: {str(e)}")
        
        # View upcoming schedule
        st.subheader("Upcoming Schedule")
        upcoming = agent.get_upcoming_schedule(days_ahead=60)
        
        if not upcoming:
            st.info("No upcoming study sessions scheduled.")
        else:
            for session in upcoming:
                with st.expander(f"{session['session_date']} - {session['series_title']}"):
                    st.write(f"**Passage:** {session['passage_title']} ({session['reference']})")
                    
                    # Display and edit role assignments
                    st.write("**Role Assignments:**")
                    for assignment in session['role_assignments']:
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            st.write(f"{assignment['role'].title().replace('_', ' ')}:")
                        with col2:
                            # Get available members for dropdown
                            conn = get_db_connection()
                            members = conn.execute(
                                'SELECT id, name FROM members WHERE is_active = 1 ORDER BY name'
                            ).fetchall()
                            member_names = ["(Unassigned)"] + [m['name'] for m in members]
                            member_ids = [None] + [m['id'] for m in members]
                            
                            # Find current selection
                            current_idx = 0  # Default to "Unassigned"
                            if assignment['member_id']:
                                for i, m_id in enumerate(member_ids):
                                    if m_id == assignment['member_id']:
                                        current_idx = i
                                        break
                            
                            # Create dropdown
                            new_member_idx = st.selectbox(
                                f"Select {assignment['role']}",
                                range(len(member_names)),
                                index=current_idx,
                                format_func=lambda i: member_names[i],
                                key=f"role_{session['session_date']}_{assignment['role']}"
                            )
                            
                            # Update role if changed
                            if new_member_idx != current_idx:
                                new_member_id = member_ids[new_member_idx]
                                if new_member_id:
                                    try:
                                        update_role_assignment(
                                            session_date=session['session_date'],
                                            role=assignment['role'],
                                            member_id=new_member_id
                                        )
                                        st.experimental_rerun()  # Refresh the UI
                                    except Exception as e:
                                        st.error(f"Error updating role: {str(e)}")
                    
                    # Generate materials button
                    if st.button("Generate Study Materials", key=f"gen_{session['session_date']}"):
                        with st.spinner("Generating study materials..."):
                            try:
                                # Find the series ID for this session
                                conn = get_db_connection()
                                series = conn.execute(
                                    'SELECT id FROM series WHERE title = ?',
                                    (session['series_title'],)
                                ).fetchone()
                                
                                if series:
                                    results = agent.generate_materials(series_id=series['id'])
                                    st.success(f"Generated {len(results)} study guides")
                                else:
                                    st.error("Could not find series in database")
                            except Exception as e:
                                st.error(f"Error generating materials: {str(e)}")
                            finally:
                                conn.close()
    
    elif page == "Generate Materials":
        st.header("📝 Generate Study Materials")
        
        # Select series to generate materials for
        conn = get_db_connection()
        series_list = conn.execute('SELECT * FROM series ORDER BY start_date DESC').fetchall()
        
        if not series_list:
            st.warning("No study series found. Create a series first.")
        else:
            series_options = {f"{s['title']} ({s['theme']})": s['id'] for s in series_list}
            selected_series = st.selectbox(
                "Select a series to generate materials for:",
                options=list(series_options.keys())
            )
            
            if st.button("Generate Materials", type="primary"):
                series_id = series_options[selected_series]
                with st.spinner("Generating study materials..."):
                    try:
                        results = agent.generate_materials(series_id=series_id)
                        st.success(f"Successfully generated {len(results)} study guides!")
                        
                        # Show preview of generated files
                        st.subheader("Generated Files")
                        for result in results:
                            st.write(f"- {result['title']} ({result['reference']}): `{result['filepath']}`")
                        
                    except Exception as e:
                        st.error(f"Error generating materials: {str(e)}")
        
        conn.close()

if __name__ == "__main__":
    # This allows running the Streamlit app directly: python -m app.kambari_agent
    run_streamlit_app()