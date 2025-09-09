#!/usr/bin/env python3
"""
Build search index from text files in output/txt directory.
Stores page content line-by-line in PostgreSQL database for granular search functionality.
Drops and recreates all tables on each run for clean indexing.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional

import psycopg2
from psycopg2 import sql


def get_database_connection(dbname: str = "herbert") -> psycopg2.extensions.connection:
    """
    Connect to PostgreSQL database.
    Similar to Perl's DBI->connect(), but with different syntax.
    """
    try:
        conn = psycopg2.connect(
            host="localhost",
            database=dbname,
            user=os.getenv("POSTGRES_RW_USER"),
            password=os.getenv("POSTGRES_RW_PASSWORD"),
        )
        return conn
    except psycopg2.Error as e:
        print(f"Database connection failed: {e}", file=sys.stderr)
        sys.exit(1)


def drop_all_tables(conn: psycopg2.extensions.connection) -> None:
    """
    Drop all tables in the database.
    Similar to Perl: $dbh->do("DROP TABLE IF EXISTS tablename CASCADE");
    """
    with conn.cursor() as cur:
        # Get all table names
        cur.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
        """)
        tables = cur.fetchall()
        
        for (table_name,) in tables:
            cur.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
            print(f"Dropped table: {table_name}")
        
        conn.commit()


def create_search_table(conn: psycopg2.extensions.connection) -> None:
    """
    Create the search_data table for line-by-line storage.
    In Perl, you'd typically use raw SQL strings with DBI.
    """
    create_table_sql = """
    CREATE TABLE search_data (
        id SERIAL PRIMARY KEY,
        page_number INTEGER NOT NULL,
        line_number INTEGER NOT NULL,
        content TEXT NOT NULL,
        UNIQUE(page_number, line_number)
    )
    """
    
    with conn.cursor() as cur:
        cur.execute(create_table_sql)
        conn.commit()
        print("Created search_data table")


def extract_page_number(filename: str) -> Optional[int]:
    """
    Extract page number from filename like 'page123.txt'.
    In Perl: $filename =~ /page(\d+)\.txt/ and return $1
    Python regex is similar but uses different syntax for groups.
    """
    match = re.match(r'page(\d+)\.txt$', filename, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def scan_text_files(directory: str = "output/txt") -> List[Tuple[int, int, str]]:
    """
    Scan directory for .txt files and extract content line by line.
    Returns tuples of (page_number, line_number, line_content).
    Similar to Perl's File::Find or glob("$dir/*.txt"), but now processing line by line.
    """
    txt_dir = Path(directory)
    
    if not txt_dir.exists():
        print(f"Directory {directory} does not exist", file=sys.stderr)
        return []
    
    lines_data = []
    
    # In Perl: for my $file (glob("$dir/*.txt")) { ... }
    for txt_file in txt_dir.glob("*.txt"):
        page_number = extract_page_number(txt_file.name)
        
        if page_number is None:
            print(f"Skipping file {txt_file.name} - couldn't extract page number")
            continue
        
        try:
            # In Perl: open(my $fh, '<', $file) or die $!;
            # while (my $line = <$fh>) { ... }
            with open(txt_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            line_number = 1
            for line in lines:
                line_content = line.strip()
                
                # Skip empty lines
                if line_content:
                    lines_data.append((page_number, line_number, line_content))
                    line_number += 1
            
            print(f"Found page {page_number}: {txt_file.name} ({line_number-1} lines)")
                
        except (IOError, UnicodeDecodeError) as e:
            print(f"Error reading {txt_file}: {e}", file=sys.stderr)
            continue
    
    return lines_data


def insert_lines(conn: psycopg2.extensions.connection, 
                lines_data: List[Tuple[int, int, str]]) -> None:
    """
    Insert line data into database.
    Similar to Perl's prepare/execute pattern with DBI.
    """
    insert_sql = """
    INSERT INTO search_data (page_number, line_number, content)
    VALUES (%s, %s, %s)
    """
    
    with conn.cursor() as cur:
        try:
            # In Perl: $sth->execute($page_num, $line_num, $content) for each row
            # Python can do executemany for better performance
            cur.executemany(insert_sql, lines_data)
            conn.commit()
            print(f"Successfully inserted {len(lines_data)} lines")
            
        except psycopg2.Error as e:
            conn.rollback()
            print(f"Database insert failed: {e}", file=sys.stderr)
            raise


def main():
    """
    Main function - similar to Perl's typical script structure.
    In Perl you might just have the main logic at script level.
    """
    print("Building search index...")
    
    # Connect to database
    conn = get_database_connection()
    
    try:
        # Drop all existing tables and recreate
        drop_all_tables(conn)
        
        # Create new table structure
        create_search_table(conn)
        
        # Scan and process text files line by line
        lines_data = scan_text_files()
        
        if not lines_data:
            print("No valid text files found to index")
            return
        
        # Insert new data
        insert_lines(conn, lines_data)
        
        print(f"Search index build complete! Indexed {len(lines_data)} lines.")
        
    except Exception as e:
        print(f"Build failed: {e}", file=sys.stderr)
        sys.exit(1)
        
    finally:
        # In Perl: $dbh->disconnect() or similar
        conn.close()


if __name__ == "__main__":
    main()
