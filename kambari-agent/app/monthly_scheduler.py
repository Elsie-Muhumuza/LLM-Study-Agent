import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
import random
import json
from pathlib import Path
import re
from enum import Enum

# Import the question generator for series content
from .question_generator import generate_study_guide

class SeriesType(Enum):
    CUSTOM = "custom"
    WOMEN_OF_FAITH = "women_of_faith"
    BOOK_STUDY = "book_study"
    TOPICAL = "topical"

@dataclass
class BiblePassage:
    reference: str
    title: str
    summary: str = ""
    key_verses: List[str] = field(default_factory=list)
    discussion_questions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'reference': self.reference,
            'title': self.title,
            'summary': self.summary,
            'key_verses': self.key_verses,
            'discussion_questions': self.discussion_questions
        }

class BibleStudyGenerator:
    """Handles generation of Bible study content."""
    
    @staticmethod
    def generate_series(topic: str, passages: List[Dict[str, Any]]) -> List[BiblePassage]:
        """Generate a series on a given topic."""
        # Convert to BiblePassage objects
        series_passages = []
        for passage in passages:
            # Generate discussion questions using the question generator
            questions = []
            try:
                # Try to generate questions, but have fallback questions ready
                study_guide = generate_study_guide(passage['reference'], passage['title'])
                questions = study_guide.get('discussion', [])[:3]  # Get first 3 discussion questions
            except:
                # Fallback questions if generation fails
                questions = [
                    f"What can we learn from {passage['title']} about {topic}?",
                    f"How does {passage['title']} reveal God's character in relation to {topic}?",
                    f"What practical lessons can we apply from {passage['title']} to our own faith journey regarding {topic}?"
                ]
            
            # Create a summary
            themes = ", ".join(passage.get('themes', []))
            summary = f"This study explores {passage['title']}, focusing on {themes}. " \
                     f"Key passages include {passage['reference']} which reveal the biblical perspective on {topic}."
            
            passage_obj = BiblePassage(
                reference=passage['reference'],
                title=passage['title'],
                summary=summary,
                key_verses=passage.get('key_verses', []),
                discussion_questions=questions
            )
            series_passages.append(passage_obj)
        
        return series_passages

    @staticmethod
    def generate_women_of_faith_series() -> List[BiblePassage]:
        """Generate a series on Women of Faith from the Bible."""
        women_of_faith = [
            {
                'reference': 'Genesis 16:1-16; 21:8-21',
                'name': 'Hagar',
                'title': 'Hagar: Seen by God',
                'key_verses': ['Genesis 16:13', 'Genesis 21:17-18'],
                'themes': ['God sees the outcast', 'Divine provision in desolation']
            },
            {
                'reference': 'Exodus 1:15-2:10',
                'name': 'Shiphrah & Puah',
                'title': 'Shiphrah & Puah: Courageous Midwives',
                'key_verses': ['Exodus 1:17', 'Exodus 1:20-21'],
                'themes': ['Courageous faith', 'Civil disobedience for God']
            },
            {
                'reference': 'Joshua 2:1-24; 6:22-25',
                'name': 'Rahab',
                'title': 'Rahab: Faith in Action',
                'key_verses': ['Joshua 2:9-11', 'Hebrews 11:31'],
                'themes': ['Faith demonstrated through action', 'Redemption']
            },
            {
                'reference': 'Judges 4:1-5:31',
                'name': 'Deborah',
                'title': 'Deborah: Prophetess and Leader',
                'key_verses': ['Judges 4:4-5', 'Judges 5:31'],
                'themes': ['Leadership', 'Hearing God\'s voice', 'Obedience']
            },
            {
                'reference': 'Ruth 1:1-4:22',
                'name': 'Ruth',
                'title': 'Ruth: Loyalty and Redemption',
                'key_verses': ['Ruth 1:16-17', 'Ruth 4:14-15'],
                'themes': ['Loyalty', 'Redemption', 'God\'s providence']
            },
            {
                'reference': '1 Samuel 1:1-2:11',
                'name': 'Hannah',
                'title': 'Hannah: A Prayerful Heart',
                'key_verses': ['1 Samuel 1:15-16', '1 Samuel 1:27-28'],
                'themes': ['Persistent prayer', 'Surrendering to God']
            },
            {
                'reference': '2 Kings 22:14-20',
                'name': 'Huldah',
                'title': 'Huldah: The Forgotten Prophetess',
                'key_verses': ['2 Kings 22:15-16', '2 Kings 22:19-20'],
                'themes': ['Speaking truth to power', 'Spiritual influence']
            },
            {
                'reference': 'Esther 1:1-10:3',
                'name': 'Esther',
                'title': 'Esther: For Such a Time as This',
                'key_verses': ['Esther 4:14', 'Esther 4:16'],
                'themes': ['Divine timing', 'Courage in crisis', 'God\'s providence']
            },
            {
                'reference': 'Luke 1:26-56',
                'name': 'Mary (Mother of Jesus)',
                'title': 'Mary: Favored by God',
                'key_verses': ['Luke 1:30-33', 'Luke 1:46-49'],
                'themes': ['Surrender to God', 'Faith in God\'s promises']
            },
            {
                'reference': 'Luke 2:36-38',
                'name': 'Anna',
                'title': 'Anna: Faithful Witness',
                'key_verses': ['Luke 2:37-38'],
                'themes': ['Faithfulness in prayer', 'Witnessing Christ']
            },
            {
                'reference': 'John 4:1-42',
                'name': 'The Samaritan Woman',
                'title': 'The Woman at the Well: Transformed by Truth',
                'key_verses': ['John 4:13-14', 'John 4:28-29', 'John 4:39'],
                'themes': ['Living water', 'Witnessing', 'Breaking barriers']
            },
            {
                'reference': 'Luke 8:43-48',
                'name': 'The Bleeding Woman',
                'title': 'Touching the Hem: A Leap of Faith',
                'key_verses': ['Luke 8:47-48'],
                'themes': ['Faith that heals', 'Touching Jesus']
            },
            {
                'reference': 'John 12:1-8',
                'name': 'Mary of Bethany',
                'title': 'Mary: Extravagant Worship',
                'key_verses': ['John 12:3', 'John 12:7-8'],
                'themes': ['Worship', 'Sacrifice', 'Prioritizing Jesus']
            },
            {
                'reference': 'Acts 9:36-42',
                'name': 'Dorcas',
                'title': 'Dorcas: Full of Good Works',
                'key_verses': ['Acts 9:36', 'Acts 9:39'],
                'themes': ['Serving others', 'Impactful living']
            },
            {
                'reference': 'Acts 16:11-15, 40',
                'name': 'Lydia',
                'title': 'Lydia: A Woman of Influence',
                'key_verses': ['Acts 16:14-15', 'Acts 16:40'],
                'themes': ['Hospitality', 'Leadership', 'Generosity']
            },
            {
                'reference': 'Acts 18:24-28',
                'name': 'Priscilla',
                'title': 'Priscilla: Teacher of the Faith',
                'key_verses': ['Acts 18:26', 'Romans 16:3-4'],
                'themes': ['Teaching', 'Partnership in ministry']
            },
            {
                'reference': '2 John 1:1-13',
                'name': 'The Chosen Lady',
                'title': 'The Chosen Lady: A Faithful Leader',
                'key_verses': ['2 John 1:4-6'],
                'themes': ['Walking in truth', 'Love and obedience']
            },
            {
                'reference': '1 Peter 3:1-6',
                'name': 'Sarah',
                'title': 'Sarah: A Woman of Faith',
                'key_verses': ['1 Peter 3:5-6', 'Hebrews 11:11'],
                'themes': ['Faith in God\'s promises', 'Inner beauty']
            },
            {
                'reference': '2 Timothy 1:5',
                'name': 'Lois and Eunice',
                'title': 'Lois and Eunice: A Legacy of Faith',
                'key_verses': ['2 Timothy 1:5', '2 Timothy 3:14-15'],
                'themes': ['Spiritual legacy', 'Passing faith to the next generation']
            },
            {
                'reference': 'Philippians 4:2-3',
                'name': 'Euodia and Syntyche',
                'title': 'Euodia and Syntyche: Resolving Conflict',
                'key_verses': ['Philippians 4:2-3'],
                'themes': ['Conflict resolution', 'Unity in Christ']
            },
            {
                'reference': 'Romans 16:1-2',
                'name': 'Phoebe',
                'title': 'Phoebe: A Servant of the Church',
                'key_verses': ['Romans 16:1-2'],
                'themes': ['Service', 'Church leadership']
            },
            {
                'reference': 'Romans 16:6',
                'name': 'Mary',
                'title': 'Mary: A Woman Who Worked Hard',
                'key_verses': ['Romans 16:6'],
                'themes': ['Diligence', 'Service']
            },
            {
                'reference': 'Romans 16:7',
                'name': 'Junia',
                'title': 'Junia: Outstanding Among the Apostles',
                'key_verses': ['Romans 16:7'],
                'themes': ['Apostolic ministry', 'Faithfulness']
            },
            {
                'reference': 'Romans 16:12',
                'name': 'Tryphena, Tryphosa, and Persis',
                'title': 'Women Who Worked Hard in the Lord',
                'key_verses': ['Romans 16:12'],
                'themes': ['Laboring for Christ', 'Faithful service']
            },
            {
                'reference': 'Romans 16:15',
                'name': 'Julia and the Sister of Nereus',
                'title': 'Julia and the Sister of Nereus: Faithful Saints',
                'key_verses': ['Romans 16:15'],
                'themes': ['Faithfulness', 'Community']
            }
        ]
        
        return BibleStudyGenerator.generate_series("Women of Faith", women_of_faith)

@dataclass
class Member:
    id: int
    name: str
    phone: str
    email: str = ""
    is_active: bool = True

@dataclass
class Session:
    date: str  # YYYY-MM-DD
    topic: str
    passage: str
    roles: Dict[str, Optional[Member]]  # role_name: assigned_member

class MonthlyScheduler:
    """Handles scheduling of Bible study sessions with automatic content generation."""
    
    ROLES = [
        "worship_leader",
        "prayer_leader",
        "scripture_reader",
        "discussion_leader",
        "hospitality"
    ]
    
    def __init__(self, db_path: str = None):
        """Initialize the scheduler with database path."""
        self.db_path = db_path or str(Path(__file__).parent.parent / 'kambari.db')
        self.conn = None
        self.members: List[Member] = []
        self.sessions: List[Session] = []
        self.role_history = defaultdict(deque)
        self.bible_generator = BibleStudyGenerator()
        
    def create_series(self, series_type: SeriesType, **kwargs) -> List[Session]:
        """Create a new Bible study series.
        
        Args:
            series_type: Type of series to create (e.g., WOMEN_OF_FAITH)
            **kwargs: Additional parameters for the series
                - start_date: Start date of the series (YYYY-MM-DD)
                - frequency: 'weekly' or 'biweekly' (default: 'weekly')
                - excluded_days: List of weekdays to exclude (0=Monday, 6=Sunday)
                
        Returns:
            List of scheduled Session objects
        """
        if series_type == SeriesType.WOMEN_OF_FAITH:
            return self._create_women_of_faith_series(**kwargs)
        elif series_type == SeriesType.BOOK_STUDY:
            return self._create_book_study_series(**kwargs)
        elif series_type == SeriesType.TOPICAL:
            return self._create_topical_series(**kwargs)
        else:
            raise ValueError(f"Unsupported series type: {series_type}")
    
    def _create_women_of_faith_series(self, start_date: str = None, 
                                    frequency: str = 'weekly',
                                    excluded_days: List[int] = None) -> List[Session]:
        """Create a series on Women of Faith from the Bible."""
        # Set default start date to next Friday if not provided
        if not start_date:
            today = datetime.now()
            days_until_friday = (4 - today.weekday()) % 7  # 4 = Friday (0=Monday)
            if days_until_friday == 0 and today.hour >= 18:  # If it's Friday evening
                days_until_friday = 7  # Schedule for next Friday
            start_date = (today + timedelta(days=days_until_friday)).strftime('%Y-%m-%d')
        
        # Get all women of faith passages
        passages = self.bible_generator.generate_women_of_faith_series()
        
        # Schedule the sessions
        sessions = []
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        
        for i, passage in enumerate(passages):
            # Skip excluded days (e.g., weekends)
            while excluded_days and current_date.weekday() in excluded_days:
                current_date += timedelta(days=1)
            
            # Create session
            session = Session(
                date=current_date.strftime('%Y-%m-%d'),
                topic=passage.title,
                passage=passage.reference,
                roles={role: None for role in self.ROLES}
            )
            sessions.append(session)
            
            # Move to next session date
            if frequency == 'weekly':
                current_date += timedelta(weeks=1)
            elif frequency == 'biweekly':
                current_date += timedelta(weeks=2)
            else:
                current_date += timedelta(weeks=1)  # Default to weekly
        
        self.sessions = sessions
        return sessions
    
    def _create_book_study_series(self, **kwargs):
        """Create a book study series (to be implemented)."""
        raise NotImplementedError("Book study series coming soon!")
    
    def _create_topical_series(self, **kwargs):
        """Create a topical study series (to be implemented)."""
        raise NotImplementedError("Topical study series coming soon!")
    
    def get_connection(self):
        """Get a database connection."""
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close_connection(self):
        """Close the database connection if open."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def load_members(self):
        """Load active members from the database."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, phone, email, is_active 
            FROM members 
            WHERE is_active = 1
        """)
        self.members = [
            Member(
                id=row['id'],
                name=row['name'],
                phone=row['phone'],
                email=row.get('email', ''),
                is_active=bool(row['is_active'])
            ) for row in cursor.fetchall()
        ]
        return self.members
    
    def load_role_history(self, months: int = 3):
        """Load role assignment history for fair distribution."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT member_id, role, session_date 
            FROM schedule_roles 
            WHERE session_date >= date('now', ?)
            ORDER BY session_date DESC
        """, (f"-{months} months",))
        
        for row in cursor.fetchall():
            member_id = row['member_id']
            role = row['role']
            if len(self.role_history[(member_id, role)]) < 3:
                self.role_history[(member_id, role)].append(row['session_date'])
    
    def assign_roles(self):
        """Assign roles to members for all sessions."""
        if not self.sessions:
            raise ValueError("No sessions to assign roles to. Create a series first.")
        
        self.load_members()
        self.load_role_history()
        
        # Shuffle members to ensure fairness
        available_members = self.members.copy()
        random.shuffle(available_members)
        
        for session in self.sessions:
            # Get members who haven't had roles recently
            available_for_session = [
                m for m in available_members 
                if self._can_assign_role(m.id, session.date)
            ]
            
            # If not enough available members, use all members
            if len(available_for_session) < len(self.ROLES):
                available_for_session = available_members.copy()
            
            # Assign roles
            for role in self.ROLES:
                assigned = False
                for member in available_for_session:
                    if self._can_assign_role(member.id, session.date, role):
                        session.roles[role] = member
                        available_for_session.remove(member)
                        assigned = True
                        break
                
                # If no member could be assigned, leave as None
                if not assigned:
                    session.roles[role] = None
    
    def _can_assign_role(self, member_id: int, date: str, role: str = None) -> bool:
        """Check if a member can be assigned a role on a given date."""
        # Check if member has this role too recently
        if role and (member_id, role) in self.role_history:
            last_assignment = self.role_history[(member_id, role)][0]  # Most recent
            last_date = datetime.strptime(last_assignment, '%Y-%m-%d').date()
            current_date = datetime.strptime(date, '%Y-%m-%d').date()
            if (current_date - last_date).days < 14:  # At least 2 weeks between same role
                return False
        
        # Check if member is already assigned a role in this session
        for session in self.sessions:
            if session.date == date and any(
                m and m.id == member_id 
                for m in session.roles.values()
            ):
                return False
        
        return True
    
    def save_to_database(self):
        """Save the generated schedule to the database."""
        if not self.sessions:
            raise ValueError("No sessions to save. Create a series first.")
            
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            for session in self.sessions:
                # Insert or update the session
                cursor.execute("""
                    INSERT OR REPLACE INTO schedule 
                    (session_date, topic, passage) 
                    VALUES (?, ?, ?)
                """, (session.date, session.topic, session.passage))
                
                # Delete existing role assignments
                cursor.execute(
                    "DELETE FROM schedule_roles WHERE session_date = ?",
                    (session.date,)
                )
                
                # Insert new role assignments
                for role, member in session.roles.items():
                    if member:  # Only insert if a member is assigned
                        cursor.execute("""
                            INSERT INTO schedule_roles 
                            (session_date, role, member_id) 
                            VALUES (?, ?, ?)
                        """, (session.date, role, member.id))
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"Error saving to database: {e}")
            return False
    
    def to_dict(self) -> List[Dict]:
        """Convert schedule to a list of dictionaries."""
        return [
            {
                'date': session.date,
                'topic': session.topic,
                'passage': session.passage,
                'roles': {
                    role: member.name if member else None
                    for role, member in session.roles.items()
                }
            }
            for session in self.sessions
        ]
    
    def print_schedule(self):
        """Print the schedule in a human-readable format."""
        for session in self.sessions:
            print(f"\n📅 {session.date} - {session.topic} ({session.passage})")
            print("=" * 50)
            for role, member in session.roles.items():
                member_name = member.name if member else "Unassigned"
                print(f"• {role.replace('_', ' ').title()}: {member_name}")
            print()

def create_monthly_schedule():
    """CLI function to create a monthly schedule."""
    import click
    from datetime import datetime
    
    # Get current year and month
    today = datetime.now()
    year = click.prompt("Enter year", type=int, default=today.year)
    month = click.prompt("Enter month (1-12)", type=click.IntRange(1, 12), default=today.month)
    
    # Series type selection
    click.echo("\nSelect series type:")
    for i, series_type in enumerate(SeriesType, 1):
        click.echo(f"{i}. {series_type.name.replace('_', ' ').title()}")
    
    series_choice = click.prompt("Enter your choice", type=click.IntRange(1, len(SeriesType)))
    series_type = list(SeriesType)[series_choice - 1]
    
    # Create scheduler
    scheduler = MonthlyScheduler()
    
    try:
        # Generate the series
        if series_type == SeriesType.WOMEN_OF_FATIH:
            click.echo("\nGenerating Women of Faith series...")
            start_date = click.prompt(
                "Start date (YYYY-MM-DD, leave blank for next Friday)",
                default="",
                show_default=False
            )
            frequency = click.prompt(
                "Frequency (weekly/biweekly)",
                type=click.Choice(['weekly', 'biweekly'], case_sensitive=False),
                default='weekly'
            )
            
            # Generate the series
            sessions = scheduler.create_series(
                series_type=series_type,
                start_date=start_date if start_date else None,
                frequency=frequency,
                excluded_days=[5, 6]  # Exclude weekends
            )
        
        # Assign roles
        if click.confirm("\nWould you like to assign roles automatically?", default=True):
            scheduler.assign_roles()
        
        # Show preview
        click.echo("\n📋 Generated Schedule Preview:")
        scheduler.print_schedule()
        
        # Save to database
        if click.confirm("\nSave this schedule to the database?", default=True):
            if scheduler.save_to_database():
                click.echo("✅ Schedule saved successfully!")
                
                # Export to JSON
                if click.confirm("Export schedule to JSON file?", default=True):
                    filename = f"bible_study_schedule_{year}_{month:02d}.json"
                    with open(filename, 'w') as f:
                        json.dump(scheduler.to_dict(), f, indent=2)
                    click.echo(f"📄 Schedule exported to {filename}")
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
    finally:
        scheduler.close_connection()

if __name__ == "__main__":
    create_monthly_schedule()
    
    def load_role_history(self, months: int = 3):
        """Load role assignment history for fair distribution."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get all past role assignments
        cursor.execute("""
            SELECT member_id, role, session_date 
            FROM schedule 
            WHERE session_date >= date('now', ?)
            ORDER BY session_date DESC
        """, (f"-{months} months",))
        
        # Store the last 3 assignments per member per role
        for row in cursor.fetchall():
            member_id = row['member_id']
            role = row['role']
            if len(self.role_history[(member_id, role)]) < 3:
                self.role_history[(member_id, role)].append(row['session_date'])
    
    def generate_schedule(
        self, 
        year: int, 
        month: int, 
        topics: List[Dict[str, str]],
        excluded_days: List[int] = [5, 6]  # Default: exclude weekends
    ) -> List[Session]:
        """Generate a schedule for the specified month."""
        self.load_members()
        self.load_role_history()
        
        # Get all Fridays in the month (or your meeting day)
        sessions = []
        date = datetime(year, month, 1)
        topic_index = 0
        
        while date.month == month:
            # Skip excluded days (0=Monday, 6=Sunday)
            if date.weekday() not in excluded_days:
                if topic_index < len(topics):
                    topic = topics[topic_index]
                    sessions.append(Session(
                        date=date.strftime('%Y-%m-%d'),
                        topic=topic['title'],
                        passage=topic['passage'],
                        roles={role: None for role in self.ROLES}
                    ))
                    topic_index += 1
            date += timedelta(days=1)
        
        self.sessions = sessions
        return sessions
    
    def assign_roles(self):
        """Assign roles to members for all sessions."""
        if not self.sessions:
            raise ValueError("No sessions to assign roles to. Generate schedule first.")
        
        # Shuffle members to ensure fairness
        available_members = self.members.copy()
        random.shuffle(available_members)
        
        for session in self.sessions:
            # Get members who haven't had roles recently
            available_for_session = [
                m for m in available_members 
                if self._can_assign_role(m.id, session.date)
            ]
            
            # If not enough available members, use all members
            if len(available_for_session) < len(self.ROLES):
                available_for_session = available_members.copy()
            
            # Assign roles
            for role in self.ROLES:
                assigned = False
                for member in available_for_session:
                    if self._can_assign_role(member.id, session.date, role):
                        session.roles[role] = member
                        available_for_session.remove(member)
                        assigned = True
                        break
                
                # If no member could be assigned, assign None
                if not assigned:
                    session.roles[role] = None
    
    def _can_assign_role(self, member_id: int, date: str, role: str = None) -> bool:
        """Check if a member can be assigned a role on a given date."""
        # Check if member has this role too recently
        if role and (member_id, role) in self.role_history:
            last_assignment = self.role_history[(member_id, role)][0]  # Most recent
            last_date = datetime.strptime(last_assignment, '%Y-%m-%d').date()
            current_date = datetime.strptime(date, '%Y-%m-%d').date()
            if (current_date - last_date).days < 14:  # At least 2 weeks between same role
                return False
        
        # Check if member is already assigned a role in this session
        for session in self.sessions:
            if session.date == date and any(
                m and m.id == member_id 
                for m in session.roles.values()
            ):
                return False
        
        return True
    
    def save_to_database(self):
        """Save the generated schedule to the database."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            for session in self.sessions:
                # Insert or update the session
                cursor.execute("""
                    INSERT OR REPLACE INTO schedule 
                    (session_date, topic, passage) 
                    VALUES (?, ?, ?)
                """, (session.date, session.topic, session.passage))
                
                # Get the session ID
                session_id = cursor.lastrowid
                
                # Delete existing role assignments
                cursor.execute(
                    "DELETE FROM schedule_roles WHERE session_date = ?",
                    (session.date,)
                )
                
                # Insert new role assignments
                for role, member in session.roles.items():
                    if member:  # Only insert if a member is assigned
                        cursor.execute("""
                            INSERT INTO schedule_roles 
                            (session_date, role, member_id) 
                            VALUES (?, ?, ?)
                        """, (session.date, role, member.id))
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"Error saving to database: {e}")
            return False
    
    def to_dict(self) -> List[Dict]:
        """Convert schedule to a list of dictionaries."""
        return [
            {
                'date': session.date,
                'topic': session.topic,
                'passage': session.passage,
                'roles': {
                    role: member.name if member else None
                    for role, member in session.roles.items()
                }
            }
            for session in self.sessions
        ]
    
    def print_schedule(self):
        """Print the schedule in a human-readable format."""
        for session in self.sessions:
            print(f"\n📅 {session.date} - {session.topic} ({session.passage})")
            print("=" * 50)
            for role, member in session.roles.items():
                member_name = member.name if member else "Unassigned"
                print(f"• {role.replace('_', ' ').title()}: {member_name}")
            print()

def create_monthly_schedule():
    """CLI function to create a monthly schedule."""
    import click
    from datetime import datetime
    
    # Get current year and month
    today = datetime.now()
    year = click.prompt("Enter year", type=int, default=today.year)
    month = click.prompt("Enter month (1-12)", type=click.IntRange(1, 12), default=today.month)
    
    # Get topics for the month
    topics = []
    click.echo("\nEnter topics for each session (leave topic blank to finish):")
    while True:
        topic = click.prompt("\nTopic", default="", show_default=False)
        if not topic:
            break
        passage = click.prompt("Bible Passage (e.g., John 3:16-17)")
        topics.append({"title": topic, "passage": passage})
    
    if not topics:
        click.echo("No topics provided. Exiting.")
        return
    
    # Generate schedule
    scheduler = MonthlyScheduler()
    try:
        click.echo(f"\nGenerating schedule for {month}/{year}...")
        scheduler.generate_schedule(year, month, topics)
        scheduler.assign_roles()
        
        # Show preview
        click.echo("\n📋 Generated Schedule Preview:")
        scheduler.print_schedule()
        
        # Confirm before saving
        if click.confirm("\nSave this schedule to the database?", default=True):
            if scheduler.save_to_database():
                click.echo("✅ Schedule saved successfully!")
                
                # Export to JSON
                if click.confirm("Export schedule to JSON file?", default=True):
                    filename = f"bible_study_schedule_{year}_{month:02d}.json"
                    with open(filename, 'w') as f:
                        json.dump(scheduler.to_dict(), f, indent=2)
                    click.echo(f"📄 Schedule exported to {filename}")
            else:
                click.echo("❌ Failed to save schedule.")
                
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
    finally:
        scheduler.close_connection()

if __name__ == "__main__":
    create_monthly_schedule()
