import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Any
import pandas as pd
from collections import defaultdict

class MonthlyReport:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(Path(__file__).parent.parent / 'kambari.db')
        self.conn = None
        
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
    
    def get_monthly_attendance(self, year: int = None, month: int = None) -> Dict[str, Any]:
        """Generate monthly attendance and participation report."""
        if year is None or month is None:
            last_month = datetime.now() - timedelta(days=30)
            year, month = last_month.year, last_month.month
        
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"
        
        conn = self.get_connection()
        
        # Get all sessions in the month
        sessions = conn.execute('''
            SELECT p.session_date, p.passage, s.title as series_title,
                   GROUP_CONCAT(m.name || ' (' || sch.role || ')', ', ') as participants
            FROM passages p
            JOIN series s ON p.series_id = s.id
            LEFT JOIN schedule sch ON p.session_date = sch.session_date
            LEFT JOIN members m ON sch.member_id = m.id
            WHERE p.session_date >= ? AND p.session_date < ?
            GROUP BY p.session_date
            ORDER BY p.session_date
        ''', (start_date, end_date)).fetchall()
        
        # Get member participation stats
        member_stats = conn.execute('''
            SELECT 
                m.id, 
                m.name,
                COUNT(DISTINCT sch.session_date) as sessions_attended,
                COUNT(DISTINCT CASE WHEN sch.role IS NOT NULL THEN sch.role ELSE NULL END) as roles_taken,
                GROUP_CONCAT(DISTINCT sch.role) as roles_list
            FROM members m
            LEFT JOIN schedule sch ON m.id = sch.member_id
            LEFT JOIN passages p ON sch.session_date = p.session_date
            WHERE p.session_date >= ? AND p.session_date < ?
            GROUP BY m.id
            HAVING sessions_attended > 0
            ORDER BY sessions_attended DESC, roles_taken DESC
        ''', (start_date, end_date)).fetchall()
        
        # Get total sessions in the month
        total_sessions = len(sessions)
        
        # Calculate consistency metrics
        member_consistency = []
        for member in member_stats:
            consistency = (member['sessions_attended'] / total_sessions) * 100 if total_sessions > 0 else 0
            member_consistency.append({
                'name': member['name'],
                'sessions_attended': member['sessions_attended'],
                'attendance_rate': f"{consistency:.1f}%",
                'roles_taken': member['roles_taken'],
                'roles_list': member['roles_list']
            })
        
        # Get most active members (top 3)
        most_active = sorted(
            member_consistency, 
            key=lambda x: (x['sessions_attended'], x['roles_taken']), 
            reverse=True
        )[:3]
        
        # Get least active members (bottom 3 with attendance < 50%)
        least_active = [
            m for m in sorted(
                member_consistency, 
                key=lambda x: (x['sessions_attended'], x['roles_taken'])
            ) 
            if float(x['attendance_rate'].rstrip('%')) < 50
        ][:3]
        
        # Generate suggestions
        suggestions = self._generate_suggestions(member_consistency, total_sessions)
        
        return {
            'period': f"{year}-{month:02d}",
            'total_sessions': total_sessions,
            'sessions': [dict(session) for session in sessions],
            'member_stats': member_consistency,
            'most_active': [dict(m) for m in most_active],
            'least_active': [dict(m) for m in least_active],
            'suggestions': suggestions
        }
    
    def _generate_suggestions(self, member_stats: List[Dict], total_sessions: int) -> List[str]:
        """Generate suggestions based on participation data."""
        suggestions = []
        
        # Calculate overall participation rate
        active_members = len([m for m in member_stats if m['sessions_attended'] > 0])
        if active_members > 0:
            avg_attendance = sum(
                float(m['attendance_rate'].rstrip('%')) 
                for m in member_stats
            ) / active_messages
            
            if avg_attendance < 60:
                suggestions.append(
                    "📉 **Low Overall Attendance**: Consider scheduling reminder messages "
                    "earlier in the week and personally reaching out to less active members."
                )
        
        # Check role distribution
        role_counts = defaultdict(int)
        for member in member_stats:
            if member['roles_list']:
                for role in member['roles_list'].split(','):
                    role = role.strip().split('(')[-1].rstrip(')')
                    role_counts[role] += 1
        
        if role_counts:
            most_common_role = max(role_counts.items(), key=lambda x: x[1])
            least_common_role = min(role_counts.items(), key=lambda x: x[1])
            
            suggestions.append(
                f"🔄 **Role Rotation**: Consider rotating the {least_common_role[0]} role more frequently. "
                f"Currently, the {most_common_role[0]} role is the most common."
            )
        
        # Check for inactive members
        if len(member_stats) > 5:  # Only suggest if there are enough members
            inactive = [m for m in member_stats if float(m['attendance_rate'].rstrip('%')) < 30]
            if inactive:
                names = ", ".join(m['name'] for m in inactive[:3])
                if len(inactive) > 3:
                    names += f" and {len(inactive) - 3} others"
                suggestions.append(
                    f"🤝 **Re-engagement Needed**: Consider reaching out to {names} "
                    "to understand any challenges they're facing in attending."
                )
        
        # Add general suggestions
        general_suggestions = [
            "🌟 **Recognition**: Publicly acknowledge the most active members to boost morale.",
            "📱 **Engagement**: Create a WhatsApp group for quick updates and reminders.",
            "📅 **Scheduling**: Send out a monthly schedule in advance so members can plan accordingly.",
            "🔄 **Role Rotation**: Rotate roles more frequently to keep engagement high.",
            "📊 **Feedback**: Send a quick survey to understand what's working and what's not."
        ]
        
        # Ensure we always have at least 3 suggestions
        while len(suggestions) < 3 and general_suggestions:
            suggestions.append(general_suggestions.pop(0))
        
        return suggestions
    
    def generate_markdown_report(self, report_data: Dict = None, output_file: str = None) -> str:
        """Generate a markdown formatted report."""
        if report_data is None:
            report_data = self.get_monthly_attendance()
        
        markdown = [
            f"# 📊 Monthly Bible Study Report - {report_data['period']}",
            f"**Period**: {report_data['period']}\n",
            f"**Total Sessions**: {report_data['total_sessions']}\n"
        ]
        
        # Attendance Summary
        markdown.extend([
            "## 📅 Attendance Summary",
            f"- Total active participants: {len(report_data['member_stats'])}\n"
        ])
        
        # Most Active Members
        if report_data['most_active']:
            markdown.append("## 🏆 Most Active Members")
            for i, member in enumerate(report_data['most_active'], 1):
                markdown.append(
                    f"{i}. **{member['name']}** - Attended {member['sessions_attended']}/{report_data['total_sessions']} "
                    f"sessions ({member['attendance_rate']}), {member['roles_taken']} roles"
                )
            markdown.append("")
        
        # Least Active Members
        if report_data['least_active']:
            markdown.append("## 📉 Less Active Members")
            for member in report_data['least_active']:
                markdown.append(
                    f"- **{member['name']}** - Attended {member['sessions_attended']}/{report_data['total_sessions']} "
                    f"sessions ({member['attendance_rate']})"
                )
            markdown.append("")
        
        # Session Details
        markdown.append("## 📋 Session Details")
        for session in report_data['sessions']:
            markdown.append(
                f"- **{session['session_date']}**: {session['series_title']} - {session['passage']}\n"
                f"  👥 Participants: {session['participants'] or 'None'}"
            )
        markdown.append("")
        
        # Suggestions for Improvement
        markdown.append("## 💡 Suggestions for Improvement")
        for suggestion in report_data['suggestions']:
            markdown.append(f"- {suggestion}")
        
        # Add footer
        markdown.extend([
            "",
            "---",
            f"*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*"
        ])
        
        report_content = "\n".join(markdown)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"✅ Report saved to {output_file}")
        
        return report_content


def generate_monthly_report():
    """Generate and display the monthly report."""
    print("📊 Generating monthly report...")
    
    report = MonthlyReport()
    try:
        # Generate report for previous month
        today = datetime.now()
        if today.month == 1:
            year, month = today.year - 1, 12
        else:
            year, month = today.year, today.month - 1
        
        # Generate filename with month and year
        filename = f"bible_study_report_{year}_{month:02d}.md"
        
        # Generate and save the report
        report_data = report.get_monthly_attendance(year, month)
        report_content = report.generate_markdown_report(report_data, filename)
        
        # Print a preview
        print("\n" + "="*50)
        print(f"📋 Monthly Report Preview ({year}-{month:02d})")
        print("="*50)
        print(f"Total Sessions: {report_data['total_sessions']}")
        print(f"Active Members: {len(report_data['member_stats'])}")
        print("\nMost Active Members:")
        for i, member in enumerate(report_data['most_active'][:3], 1):
            print(f"  {i}. {member['name']} ({member['attendance_rate']} attendance)")
        print("\nReport saved to:", filename)
        print("="*50)
        
        return report_content
    finally:
        report.close_connection()


if __name__ == "__main__":
    generate_monthly_report()
