#!/usr/bin/env python3
"""
Script to analyze and map student names between the F2, F5, F6 files 
and the Project Stem grades file.
"""

import csv
import re
from collections import defaultdict

def normalize_name(name):
    """Normalize names for comparison by removing extra spaces and converting to lowercase"""
    return re.sub(r'\s+', ' ', name.strip().lower())

def extract_names_from_csv(filename):
    """Extract names from CSV files"""
    names = []
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if row and row[0].strip():  # Skip empty rows
                    names.append(row[0].strip())
    except Exception as e:
        print(f"Error reading {filename}: {e}")
    return names

def extract_grades_names(filename):
    """Extract student names from the grades CSV file"""
    names = []
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            next(reader)  # Skip points possible row
            for row in reader:
                if row and row[0].strip():  # Skip empty rows
                    # Extract name from quoted format "Last, First"
                    name_match = re.match(r'"([^"]+)"', row[0])
                    if name_match:
                        names.append(name_match.group(1))
                    else:
                        # Try without quotes
                        if ',' in row[0]:
                            names.append(row[0])
    except Exception as e:
        print(f"Error reading {filename}: {e}")
    return names

def find_matches(name_lists, grades_names):
    """Find matches between name lists and grades names"""
    matches = defaultdict(list)
    unmatched_grades = []
    unmatched_names = defaultdict(list)
    
    # Create normalized lookup for grades names
    grades_normalized = {}
    for grade_name in grades_names:
        normalized = normalize_name(grade_name)
        grades_normalized[normalized] = grade_name
    
    # Check each name list
    for list_name, names in name_lists.items():
        for name in names:
            # Skip header rows
            if name.lower() == "name":
                continue
                
            normalized_name = normalize_name(name)
            found_match = False
            
            # Try to find match in grades
            for grade_normalized, grade_original in grades_normalized.items():
                # Skip test user Harry Champagnat
                if "champagnat" in grade_normalized and "harry" in grade_normalized:
                    continue
                    
                # Check if first and last names match (in any order)
                name_parts = normalized_name.split()
                grade_parts = grade_normalized.split(', ')
                
                if len(name_parts) >= 2 and len(grade_parts) >= 2:
                    # Check if all parts match
                    name_set = set(name_parts)
                    grade_set = set(grade_parts[0].split() + grade_parts[1].split())
                    
                    # More flexible matching for names like "Riley Sky Mantaring" vs "Mantaring, Riley"
                    if name_set == grade_set:
                        matches[list_name].append((name, grade_original))
                        found_match = True
                        break
                    # Additional check for partial matches (e.g., "Riley Sky Mantaring" vs "Mantaring, Riley")
                    elif len(name_set) >= 2 and len(grade_set) >= 2:
                        # Check if first and last names match, ignoring middle names
                        name_first_last = {name_parts[0], name_parts[-1]}
                        grade_first_last = {grade_parts[1].split()[0], grade_parts[0].split()[0]}
                        
                        if name_first_last == grade_first_last:
                            matches[list_name].append((name, grade_original))
                            found_match = True
                            break
            
            if not found_match:
                unmatched_names[list_name].append(name)
    
    # Find unmatched grades
    matched_grades = set()
    for list_matches in matches.values():
        for _, grade_name in list_matches:
            matched_grades.add(grade_name)
    
    for grade_name in grades_names:
        # Skip test user Harry Champagnat
        if "champagnat" in grade_name.lower() and "harry" in grade_name.lower():
            continue
        if grade_name not in matched_grades:
            unmatched_grades.append(grade_name)
    
    return matches, unmatched_names, unmatched_grades

def main():
    # Extract names from each file
    f2_names = extract_names_from_csv('F2 - names.csv')
    f5_names = extract_names_from_csv('F5 - names.csv')
    f6_names = extract_names_from_csv('F6 - names.csv')
    grades_names = extract_grades_names('2025-09-13T1722_Grades-(7fac90)_CS_Python_Fundamentals.csv')
    
    print("=== STUDENT NAME ANALYSIS ===")
    print(f"F2 names: {len(f2_names)}")
    print(f"F5 names: {len(f5_names)}")
    print(f"F6 names: {len(f6_names)}")
    print(f"Grades names: {len(grades_names)}")
    print(f"Total name list students: {len(f2_names) + len(f5_names) + len(f6_names)}")
    print()
    
    # Find matches
    name_lists = {
        'F2': f2_names,
        'F5': f5_names,
        'F6': f6_names
    }
    
    matches, unmatched_names, unmatched_grades = find_matches(name_lists, grades_names)
    
    # Print results
    print("=== MATCHES FOUND ===")
    for list_name, list_matches in matches.items():
        print(f"\n{list_name} ({len(list_matches)} matches):")
        for name_list, name_grades in list_matches:
            print(f"  {name_list} -> {name_grades}")
    
    print("\n=== UNMATCHED NAMES IN LISTS ===")
    for list_name, unmatched in unmatched_names.items():
        if unmatched:
            print(f"\n{list_name} ({len(unmatched)} unmatched):")
            for name in unmatched:
                print(f"  {name}")
    
    print(f"\n=== UNMATCHED GRADES ({len(unmatched_grades)} total) ===")
    for name in unmatched_grades:
        print(f"  {name}")
    
    # Summary
    total_matches = sum(len(m) for m in matches.values())
    total_unmatched_lists = sum(len(u) for u in unmatched_names.values())
    print(f"\n=== SUMMARY ===")
    print(f"Total matches found: {total_matches}")
    print(f"Total unmatched from lists: {total_unmatched_lists}")
    print(f"Total unmatched from grades: {len(unmatched_grades)}")
    print(f"Note: Harry Champagnat (test user) excluded from analysis")
    
    # Save detailed results to file
    with open('student_mapping_results.txt', 'w', encoding='utf-8') as f:
        f.write("STUDENT NAME MAPPING ANALYSIS\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"F2 names: {len(f2_names)}\n")
        f.write(f"F5 names: {len(f5_names)}\n")
        f.write(f"F6 names: {len(f6_names)}\n")
        f.write(f"Grades names: {len(grades_names)}\n")
        f.write(f"Total name list students: {len(f2_names) + len(f5_names) + len(f6_names)}\n\n")
        
        f.write("MATCHES FOUND:\n")
        f.write("-" * 20 + "\n")
        for list_name, list_matches in matches.items():
            f.write(f"\n{list_name} ({len(list_matches)} matches):\n")
            for name_list, name_grades in list_matches:
                f.write(f"  {name_list} -> {name_grades}\n")
        
        f.write("\nUNMATCHED NAMES IN LISTS:\n")
        f.write("-" * 30 + "\n")
        for list_name, unmatched in unmatched_names.items():
            if unmatched:
                f.write(f"\n{list_name} ({len(unmatched)} unmatched):\n")
                for name in unmatched:
                    f.write(f"  {name}\n")
        
        f.write(f"\nUNMATCHED GRADES ({len(unmatched_grades)} total):\n")
        f.write("-" * 30 + "\n")
        for name in unmatched_grades:
            f.write(f"  {name}\n")
        
        f.write(f"\nSUMMARY:\n")
        f.write("-" * 10 + "\n")
        f.write(f"Total matches found: {total_matches}\n")
        f.write(f"Total unmatched from lists: {total_unmatched_lists}\n")
        f.write(f"Total unmatched from grades: {len(unmatched_grades)}\n")
        f.write(f"Note: Harry Champagnat (test user) excluded from analysis\n")
    
    print(f"\nDetailed results saved to 'student_mapping_results.txt'")

if __name__ == "__main__":
    main()
