"""
Test script to verify year linking functionality.
Run this after uploading documents for different years.

Usage:
    python test_year_linking_logic.py
"""

import sqlite3
from pathlib import Path

def check_year_linking():
    """Verify year linking in the database."""
    db_path = Path("pr_profile.db")
    
    if not db_path.exists():
        print("❌ Database not found at pr_profile.db")
        return False
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Get all profiles with year information
        cursor.execute("""
            SELECT id, employee_name, year, previous_year_profile_id
            FROM pr_profiles
            ORDER BY employee_name, year
        """)
        
        profiles = cursor.fetchall()
        
        if not profiles:
            print("⚠️  No profiles found in database")
            return False
        
        print("\n" + "="*70)
        print("PROFILE YEAR LINKING VERIFICATION")
        print("="*70)
        
        # Group by employee
        employees = {}
        for row in profiles:
            emp = row['employee_name']
            if emp not in employees:
                employees[emp] = []
            employees[emp].append(row)
        
        all_valid = True
        
        for emp_name in sorted(employees.keys()):
            emp_profiles = sorted(employees[emp_name], key=lambda x: x['year'])
            print(f"\n📋 {emp_name}")
            print("-" * 70)
            
            for idx, profile in enumerate(emp_profiles):
                prof_id = profile['id']
                year = profile['year']
                prev_id = profile['previous_year_profile_id']
                
                # Find what year the previous_id refers to
                if prev_id:
                    cursor.execute("SELECT year FROM pr_profiles WHERE id = ?", (prev_id,))
                    prev_row = cursor.fetchone()
                    prev_year = prev_row['year'] if prev_row else None
                    
                    # Verify linking
                    is_correct = (idx > 0) and (emp_profiles[idx-1]['year'] == prev_year or 
                                               prev_year is not None and prev_year < year)
                    
                    if is_correct:
                        status = "✓"
                    else:
                        status = "⚠️"
                        all_valid = False
                    
                    print(f"  {status} Year {year:4d} (ID: {prof_id:3d}) → Previous year {prev_year} (ID: {prev_id:3d})")
                else:
                    if idx == 0:
                        print(f"  ✓ Year {year:4d} (ID: {prof_id:3d}) → No previous year (first year)")
                    else:
                        print(f"  ❌ Year {year:4d} (ID: {prof_id:3d}) → No link (SHOULD HAVE LINK!)")
                        all_valid = False
            
            # Check HTML reports
            print(f"\n  HTML Reports:")
            cursor.execute(
                "SELECT year, html_report FROM pr_profiles WHERE employee_name = ? ORDER BY year",
                (emp_name,)
            )
            for row in cursor.fetchall():
                year = row['year']
                has_html = bool(row['html_report'])
                status = "✓" if has_html else "✗"
                print(f"    {status} Year {year:4d}: HTML {'generated' if has_html else 'NOT generated'}")
        
        print("\n" + "="*70)
        
        if all_valid:
            print("✅ All year links are correct!")
        else:
            print("⚠️  Some year links may be incorrect. Check logs for details.")
        
        return all_valid
        
    except Exception as e:
        print(f"❌ Error querying database: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    check_year_linking()
