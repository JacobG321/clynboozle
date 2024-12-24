# db_manager.py

import sqlite3
import datetime
import random

DB_NAME = "clynboozle.db"

class DBManager:
    """
    Manages the SQLite database connection and queries.
    """

    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name
        self.create_tables()

    def create_connection(self):
        """
        Establishes a connection to the SQLite database.
        Returns the connection object.
        """
        conn = sqlite3.connect(self.db_name)
        return conn

    def create_tables(self):
        """
        Creates the necessary tables if they do not exist:
          1. groups (id, group_name)
          2. questions (id, question, group_id, option1, option2, option3, option4, correct_option, points, category, question_type)
          3. sessions (id, created_at, is_active, time_per_question, current_turn_team_id, group_id)
          4. teams (id, session_id, team_name)
          5. players (id, team_id, player_name)
          6. session_state (id, session_id, team_id, score)
          7. session_questions (id, session_id, question_id, was_correct, answered_at)
        """
        conn = self.create_connection()
        cursor = conn.cursor()

        # 1. groups table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT NOT NULL
            );
        """)

        # 2. questions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                option1 TEXT,
                option2 TEXT,
                option3 TEXT,
                option4 TEXT,
                correct_option TEXT,
                points INTEGER DEFAULT 10,
                category TEXT,
                question_type TEXT,  -- NEW COLUMN
                FOREIGN KEY(group_id) REFERENCES groups(id)
            );
        """)

        # 3. sessions table (now has a group_id column)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                time_per_question INTEGER DEFAULT 30,
                current_turn_team_id INTEGER,
                group_id INTEGER,
                FOREIGN KEY(current_turn_team_id) REFERENCES teams(id),
                FOREIGN KEY(group_id) REFERENCES groups(id)
            );
        """)

        # 4. teams table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                team_name TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            );
        """)

        # 5. players table (optional)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                player_name TEXT NOT NULL,
                FOREIGN KEY(team_id) REFERENCES teams(id)
            );
        """)

        # 6. session_state table (tracks scores per team)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                team_id INTEGER NOT NULL,
                score INTEGER DEFAULT 0,
                FOREIGN KEY(session_id) REFERENCES sessions(id),
                FOREIGN KEY(team_id) REFERENCES teams(id)
            );
        """)

        # 7. session_questions table (tracks which questions were answered, correctness)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                was_correct INTEGER DEFAULT 0,
                answered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES sessions(id),
                FOREIGN KEY(question_id) REFERENCES questions(id)
            );
        """)

        conn.commit()
        conn.close()

    # ----------------------
    # GROUPS + QUESTIONS
    # ----------------------
    def insert_group(self, group_name):
        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO groups (group_name) 
            VALUES (?);
        """, (group_name,))
        conn.commit()
        group_id = cursor.lastrowid
        conn.close()
        return group_id

    def insert_question(self, question_data):
        """
        Inserts a question record (multiple-choice or otherwise).
        question_data keys: group_id, question, option1..4, correct_option, points, category, question_type
        """
        conn = self.create_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO questions (
                group_id,
                question,
                option1,
                option2,
                option3,
                option4,
                correct_option,
                points,
                category,
                question_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            question_data.get('group_id'),
            question_data.get('question'),
            question_data.get('option1'),
            question_data.get('option2'),
            question_data.get('option3'),
            question_data.get('option4'),
            question_data.get('correct_option'),
            question_data.get('points', 10),
            question_data.get('category'),
            question_data.get('question_type')
        ))

        conn.commit()
        question_id = cursor.lastrowid
        conn.close()
        return question_id


    def get_random_question(self, group_id=None):
        """
        Retrieves a random question from the specified group (if given).
        Returns a dict or None if no questions are found.
        """
        conn = self.create_connection()
        cursor = conn.cursor()

        if group_id:
            cursor.execute("""
                SELECT 
                    id, group_id, question, option1, option2, option3, option4,
                    correct_option, points, category, question_type
                FROM questions
                WHERE group_id = ?
                ORDER BY RANDOM() 
                LIMIT 1;
            """, (group_id,))
        else:
            cursor.execute("""
                SELECT 
                    id, group_id, question, option1, option2, option3, option4,
                    correct_option, points, category, question_type
                FROM questions
                ORDER BY RANDOM()
                LIMIT 1;
            """)

        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        return {
            'id': row[0],
            'group_id': row[1],
            'question': row[2],
            'option1': row[3],
            'option2': row[4],
            'option3': row[5],
            'option4': row[6],
            'correct_option': row[7],
            'points': row[8],
            'category': row[9],
            'question_type': row[10]
        }

    # ----------------------
    # SESSIONS
    # ----------------------
    def create_session(self, time_per_question, group_id):
        """
        Inserts a new session record into the sessions table,
        storing time_per_question and the chosen group_id.
        Returns the new session_id.
        """
        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sessions (time_per_question, is_active, group_id)
            VALUES (?, 1, ?);
        """, (time_per_question, group_id))
        conn.commit()
        session_id = cursor.lastrowid
        conn.close()
        return session_id

    def get_session(self, session_id):
        """
        Retrieves session info by session_id, including group_id.
        Returns a dict with { 'id', 'created_at', 'is_active', 'time_per_question', 'current_turn_team_id', 'group_id' }
        or None if not found.
        """
        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, created_at, is_active, time_per_question, current_turn_team_id, group_id
            FROM sessions
            WHERE id = ?;
        """, (session_id,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        return {
            'id': row[0],
            'created_at': row[1],
            'is_active': bool(row[2]),
            'time_per_question': row[3],
            'current_turn_team_id': row[4],
            'group_id': row[5]
        }

    def update_session_status(self, session_id, is_active):
        """
        Marks a session active/inactive.
        """
        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE sessions
            SET is_active = ?
            WHERE id = ?;
        """, (1 if is_active else 0, session_id))
        conn.commit()
        conn.close()

    # ----------------------
    # TEAMS + PLAYERS
    # ----------------------
    def add_team(self, session_id, team_name):
        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO teams (session_id, team_name)
            VALUES (?, ?);
        """, (session_id, team_name))
        conn.commit()
        team_id = cursor.lastrowid
        conn.close()
        return team_id

    def add_player_to_team(self, team_id, player_name):
        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO players (team_id, player_name)
            VALUES (?, ?);
        """, (team_id, player_name))
        conn.commit()
        player_id = cursor.lastrowid
        conn.close()
        return player_id

    def get_teams_for_session(self, session_id):
        conn = self.create_connection()
        cursor = conn.cursor()

        # Fetch teams
        cursor.execute("""
            SELECT id, team_name
            FROM teams
            WHERE session_id = ?;
        """, (session_id,))
        team_rows = cursor.fetchall()

        results = []
        for row in team_rows:
            team_id = row[0]
            team_name = row[1]

            # Fetch players
            cursor.execute("""
                SELECT id, player_name
                FROM players
                WHERE team_id = ?;
            """, (team_id,))
            player_rows = cursor.fetchall()

            players = []
            for p_row in player_rows:
                players.append({
                    'id': p_row[0],
                    'player_name': p_row[1]
                })

            results.append({
                'team_id': team_id,
                'team_name': team_name,
                'players': players
            })

        conn.close()
        return results

    # ----------------------
    # GAME STATE TRACKING
    # ----------------------
    def init_session_state(self, session_id, team_ids):
        conn = self.create_connection()
        cursor = conn.cursor()
        for t_id in team_ids:
            cursor.execute("""
                INSERT INTO session_state (session_id, team_id, score)
                VALUES (?, ?, 0);
            """, (session_id, t_id))
        conn.commit()
        conn.close()

    def get_session_state(self, session_id):
        conn = self.create_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT current_turn_team_id
            FROM sessions
            WHERE id = ?;
        """, (session_id,))
        row = cursor.fetchone()
        current_turn_team_id = row[0] if row else None

        # Grab scores
        cursor.execute("""
            SELECT team_id, score
            FROM session_state
            WHERE session_id = ?;
        """, (session_id,))
        rows = cursor.fetchall()

        scores = {}
        for r in rows:
            scores[r[0]] = r[1]

        conn.close()
        return {
            'current_turn_team_id': current_turn_team_id,
            'scores': scores
        }

    def update_score(self, session_id, team_id, new_score):
        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE session_state
            SET score = ?
            WHERE session_id = ? AND team_id = ?;
        """, (new_score, session_id, team_id))
        conn.commit()
        conn.close()

    def update_current_turn(self, session_id, next_team_id):
        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE sessions
            SET current_turn_team_id = ?
            WHERE id = ?;
        """, (next_team_id, session_id))
        conn.commit()
        conn.close()

    def mark_question_answered(self, session_id, question_id, was_correct):
        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO session_questions (session_id, question_id, was_correct)
            VALUES (?, ?, ?);
        """, (session_id, question_id, 1 if was_correct else 0))
        conn.commit()
        conn.close()

    def any_questions_left_for_session(self, session_id, group_id):
        """
        Returns True if there's at least one question in 'questions'
        for the given group_id that hasn't been answered in 'session_questions'.
        Otherwise returns False.
        """
        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT q.id
            FROM questions q
            WHERE q.group_id = ?
              AND q.id NOT IN (
                  SELECT question_id 
                  FROM session_questions
                  WHERE session_id = ?
              )
            LIMIT 1;
        """, (group_id, session_id))
        row = cursor.fetchone()
        conn.close()
        return (row is not None)
