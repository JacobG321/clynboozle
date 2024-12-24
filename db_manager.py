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
          2. questions (id, question, group_id, points, category, question_type, fill_in_blank_text)
          3. question_options (id, question_id, option_text, is_correct)
          4. sessions (id, created_at, is_active, time_per_question, current_turn_team_id, group_id)
          5. teams (id, session_id, team_name)
          6. players (id, team_id, player_name)
          7. session_state (id, session_id, team_id, score)
          8. session_questions (id, session_id, question_id, was_correct, answered_at)
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
        #    We'll add fill_in_blank_text as a column.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                fill_in_blank_text TEXT,  -- NEW COLUMN for fill-in blank
                points INTEGER DEFAULT 10,
                category TEXT,
                question_type TEXT,
                FOREIGN KEY(group_id) REFERENCES groups(id)
            );
        """)

        # If the column didn't exist previously, try an ALTER TABLE just in case:
        try:
            cursor.execute("ALTER TABLE questions ADD COLUMN fill_in_blank_text TEXT;")
        except:
            pass  # If it already exists, we'll ignore the error

        # 3. question_options table (NEW)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS question_options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                option_text TEXT NOT NULL,
                is_correct INTEGER DEFAULT 0,
                FOREIGN KEY(question_id) REFERENCES questions(id)
            );
        """)

        # 4. sessions table (has group_id column)
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

        # 5. teams table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                team_name TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            );
        """)

        # 6. players table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                player_name TEXT NOT NULL,
                FOREIGN KEY(team_id) REFERENCES teams(id)
            );
        """)

        # 7. session_state table
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

        # 8. session_questions table
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
        Inserts a question record and any associated options.
        
        question_data might look like:
        {
            "group_id": 1,
            "question": "Sample multiple-choice question",
            "points": 10,
            "category": "History",
            "question_type": "multiple_choice",
            "blank_text": "206" (for fill_in_blank questions),
            "options": [
                {"text": "Option A", "is_correct": False},
                {"text": "Option B", "is_correct": True},
                ...
            ]
        }
        """
        conn = self.create_connection()
        cursor = conn.cursor()

        # If question_type == "fill_in_blank", store the text in fill_in_blank_text
        # Otherwise keep it None.
        fill_text = None
        if question_data.get('question_type') == 'fill_in_blank':
            fill_text = question_data.get('blank_text', '')

        # Insert the question record
        cursor.execute("""
            INSERT INTO questions (
                group_id,
                question,
                fill_in_blank_text,
                points,
                category,
                question_type
            ) VALUES (?, ?, ?, ?, ?, ?);
        """, (
            question_data.get('group_id'),
            question_data.get('question'),
            fill_text,
            question_data.get('points', 10),
            question_data.get('category', ''),
            question_data.get('question_type', 'multiple_choice')
        ))

        question_id = cursor.lastrowid

        # If it's multiple-choice, we insert the options
        if question_data.get('question_type') == 'multiple_choice':
            for opt in question_data.get('options', []):
                cursor.execute("""
                    INSERT INTO question_options (question_id, option_text, is_correct)
                    VALUES (?, ?, ?);
                """, (question_id, opt["text"], 1 if opt["is_correct"] else 0))

        conn.commit()
        conn.close()
        return question_id

    def update_question(self, question_data):
        """
        Updates an existing question in the database and handles
        options if it's multiple choice.

        question_data might look like:
        {
            "question_id": 12,
            "group_id": 1,
            "question": "Updated question text",
            "points": 5,
            "category": "Science",
            "question_type": "fill_in_blank",
            "blank_text": "206",
            "options": [ ... ]  # only relevant for multiple_choice
        }
        """
        conn = self.create_connection()
        cursor = conn.cursor()

        fill_text = None
        if question_data.get('question_type') == 'fill_in_blank':
            fill_text = question_data.get('blank_text', '')

        # Update the main question record
        cursor.execute("""
            UPDATE questions
            SET 
                question = ?,
                fill_in_blank_text = ?,
                points = ?,
                category = ?,
                question_type = ?
            WHERE id = ?;
        """, (
            question_data.get('question'),
            fill_text,
            question_data.get('points'),
            question_data.get('category'),
            question_data.get('question_type'),
            question_data.get('question_id')
        ))

        # If multiple-choice, update the options
        if question_data.get('question_type') == 'multiple_choice':
            # Delete old options
            cursor.execute("""
                DELETE FROM question_options
                WHERE question_id = ?;
            """, (question_data["question_id"],))

            # Insert new ones
            for opt in question_data.get('options', []):
                cursor.execute("""
                    INSERT INTO question_options (question_id, option_text, is_correct)
                    VALUES (?, ?, ?);
                """, (question_data["question_id"], opt["text"], 1 if opt["is_correct"] else 0))
        else:
            # If it's not multiple_choice, remove existing options if any
            cursor.execute("""
                DELETE FROM question_options
                WHERE question_id = ?;
            """, (question_data["question_id"],))

        conn.commit()
        conn.close()

    def get_question(self, question_id):
        """
        Retrieves a single question by ID and its options (if multiple_choice),
        and fill_in_blank_text if fill_in_blank.
        Returns a dict or None if not found.
        """
        conn = self.create_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, group_id, question, fill_in_blank_text, points, category, question_type
            FROM questions
            WHERE id = ?;
        """, (question_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        question_dict = {
            'id': row[0],
            'group_id': row[1],
            'question': row[2],
            'fill_in_blank_text': row[3],  # new
            'points': row[4],
            'category': row[5],
            'question_type': row[6],
            'options': []
        }

        # If multiple choice, fetch the options from question_options
        if question_dict['question_type'] == 'multiple_choice':
            cursor.execute("""
                SELECT id, option_text, is_correct
                FROM question_options
                WHERE question_id = ?
            """, (question_id,))
            option_rows = cursor.fetchall()
            for opt_row in option_rows:
                question_dict['options'].append({
                    'id': opt_row[0],
                    'text': opt_row[1],
                    'is_correct': bool(opt_row[2])
                })

        conn.close()
        return question_dict

    def get_questions_for_group(self, group_id):
        """
        Fetches all questions for a particular group (only basic question info).
        Use get_question(question_id) to get the detailed options if needed.
        """
        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, question 
            FROM questions
            WHERE group_id = ?;
        """, (group_id,))
        rows = cursor.fetchall()
        conn.close()
        # Return a list of dicts
        return [{'id': r[0], 'question': r[1]} for r in rows]

    def delete_question(self, question_id):
        """
        Deletes a question and all its options.
        """
        conn = self.create_connection()
        cursor = conn.cursor()
        
        # First, delete options associated with the question
        cursor.execute("""
            DELETE FROM question_options
            WHERE question_id = ?;
        """, (question_id,))

        # Then delete the question itself
        cursor.execute("""
            DELETE FROM questions
            WHERE id = ?;
        """, (question_id,))

        conn.commit()
        conn.close()

    def get_random_question(self, group_id=None):
        """
        Retrieves a random question from the specified group (if given).
        Includes fill_in_blank_text if it's a fill_in_blank question,
        and fetches options if it's multiple_choice.
        Returns a dict or None if no questions are found.
        """
        conn = self.create_connection()
        cursor = conn.cursor()

        if group_id:
            cursor.execute("""
                SELECT 
                    id, group_id, question, fill_in_blank_text, points, category, question_type
                FROM questions
                WHERE group_id = ?
                ORDER BY RANDOM() 
                LIMIT 1;
            """, (group_id,))
        else:
            cursor.execute("""
                SELECT 
                    id, group_id, question, fill_in_blank_text, points, category, question_type
                FROM questions
                ORDER BY RANDOM()
                LIMIT 1;
            """)

        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        # Build the basic question dict
        question_dict = {
            'id': row[0],
            'group_id': row[1],
            'question': row[2],
            'fill_in_blank_text': row[3],   # only relevant if question_type == 'fill_in_blank'
            'points': row[4],
            'category': row[5],
            'question_type': row[6],
            'options': []                   # for multiple_choice
        }

        # If multiple_choice, fetch all options from question_options
        if question_dict['question_type'] == 'multiple_choice':
            cursor.execute("""
                SELECT id, option_text, is_correct
                FROM question_options
                WHERE question_id = ?;
            """, (question_dict['id'],))
            option_rows = cursor.fetchall()
            for opt_row in option_rows:
                question_dict['options'].append({
                    'id': opt_row[0],
                    'text': opt_row[1],
                    'is_correct': bool(opt_row[2])
                })

        conn.close()
        return question_dict


    def delete_group(self, group_id):
        """
        Deletes a group and all associated questions and options.
        """
        # 1. Find all questions for this group
        questions = self.get_questions_for_group(group_id)

        conn = self.create_connection()
        cursor = conn.cursor()

        # 2. Delete options for each question
        for q in questions:
            cursor.execute("""
                DELETE FROM question_options
                WHERE question_id = ?;
            """, (q["id"],))

        # 3. Delete questions
        cursor.execute("""
            DELETE FROM questions
            WHERE group_id = ?;
        """, (group_id,))

        # 4. Finally, delete the group itself
        cursor.execute("""
            DELETE FROM groups
            WHERE id = ?;
        """, (group_id,))

        conn.commit()
        conn.close()

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
