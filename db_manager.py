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

    # ----------------------------------------------------------------
    #                          CONNECTIONS
    # ----------------------------------------------------------------
    def create_connection(self):
        """
        Establishes a connection to the SQLite database.
        Returns the connection object.
        """
        return sqlite3.connect(self.db_name)

    def _exec_commit(self, sql, params=None):
        """
        Helper method to connect, execute a single SQL, commit, and close.
        Returns the cursor and connection if needed.
        """
        if params is None:
            params = ()
        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor, conn

    # ----------------------------------------------------------------
    #                          TABLE CREATION
    # ----------------------------------------------------------------
    def create_tables(self):
        """
        Creates the necessary tables if they do not exist:
          1. groups (id, group_name)
          2. questions (id, question, question_group_id, points, category, question_type, fill_in_blank_text)
          3. question_options (id, question_id, option_text, is_correct)
          4. sessions (id, created_at, is_active, time_per_question, current_turn_team_id, question_group_id)
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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_group_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                fill_in_blank_text TEXT,
                points INTEGER DEFAULT 10,
                category TEXT,
                question_type TEXT,
                FOREIGN KEY(question_group_id) REFERENCES groups(id)
            );
        """)

        # Attempt adding fill_in_blank_text if it didn't exist
        try:
            cursor.execute("ALTER TABLE questions ADD COLUMN fill_in_blank_text TEXT;")
        except sqlite3.OperationalError:
            pass  # Already exists, ignore

        # 3. question_options table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS question_options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                option_text TEXT NOT NULL,
                is_correct INTEGER DEFAULT 0,
                FOREIGN KEY(question_id) REFERENCES questions(id)
            );
        """)

        # 4. sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                time_per_question INTEGER DEFAULT 30,
                current_turn_team_id INTEGER,
                question_group_id INTEGER,
                FOREIGN KEY(current_turn_team_id) REFERENCES teams(id),
                FOREIGN KEY(question_group_id) REFERENCES groups(id)
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
                was_correct INTEGER,
                answered INTEGER DEFAULT 0,
                answered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES sessions(id),
                FOREIGN KEY(question_id) REFERENCES questions(id),
                UNIQUE(session_id, question_id)
            );
        """)
        
        conn.commit()
        conn.close()

    # ----------------------------------------------------------------
    #                          GROUPS + QUESTIONS
    # ----------------------------------------------------------------

    def insert_group(self, group_name):
        """
        Inserts a new row into 'groups' and returns the new group's ID.
        """
        sql = """
            INSERT INTO groups (group_name)
            VALUES (?);
        """
        cursor, conn = self._exec_commit(sql, (group_name,))
        group_id = cursor.lastrowid
        conn.close()
        return group_id

    def insert_question(self, question_data):
        """
        Inserts a question record and any associated options.

        question_data example:
        {
            "question_group_id": 1,
            "question": "Sample multiple-choice question",
            "points": 10,
            "category": "History",
            "question_type": "multiple_choice",
            "blank_text": "206",  # for fill_in_blank
            "options": [
                {"text": "Option A", "is_correct": False},
                ...
            ]
        }
        """
        fill_text = None
        if question_data.get('question_type') == 'fill_in_blank':
            fill_text = question_data.get('blank_text', '')

        sql = """
            INSERT INTO questions (
                question_group_id,
                question,
                fill_in_blank_text,
                points,
                category,
                question_type
            ) VALUES (?, ?, ?, ?, ?, ?);
        """
        params = (
            question_data.get('question_group_id'),
            question_data.get('question'),
            fill_text,
            question_data.get('points', 10),
            question_data.get('category', ''),
            question_data.get('question_type', 'multiple_choice')
        )

        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        question_id = cursor.lastrowid

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
            "question_group_id": 1,
            "question": "Updated question text",
            "points": 5,
            "category": "Science",
            "question_type": "fill_in_blank",
            "blank_text": "206",
            "options": [ ... ]  # only relevant for multiple_choice
        }
        """
        fill_text = None
        if question_data.get('question_type') == 'fill_in_blank':
            fill_text = question_data.get('blank_text', '')

        sql_update = """
            UPDATE questions
            SET
                question = ?,
                fill_in_blank_text = ?,
                points = ?,
                category = ?,
                question_type = ?
            WHERE id = ?;
        """
        params = (
            question_data.get('question'),
            fill_text,
            question_data.get('points'),
            question_data.get('category'),
            question_data.get('question_type'),
            question_data.get('question_id')
        )

        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute(sql_update, params)

        # If multiple-choice, update the options
        if question_data.get('question_type') == 'multiple_choice':
            cursor.execute("""
                DELETE FROM question_options
                WHERE question_id = ?;
            """, (question_data["question_id"],))

            for opt in question_data.get('options', []):
                cursor.execute("""
                    INSERT INTO question_options (question_id, option_text, is_correct)
                    VALUES (?, ?, ?);
                """, (
                    question_data["question_id"],
                    opt["text"],
                    1 if opt["is_correct"] else 0
                ))
        else:
            # If not multiple_choice, remove existing options if any
            cursor.execute("""
                DELETE FROM question_options
                WHERE question_id = ?;
            """, (question_data["question_id"],))

        conn.commit()
        conn.close()

    def get_question(self, question_id):
        """
        Retrieves a single question by ID and its options (if multiple_choice).
        """
        sql = """
            SELECT
                id, question_group_id, question, fill_in_blank_text, 
                points, category, question_type
            FROM questions
            WHERE id = ?;
        """
        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute(sql, (question_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        question_dict = {
            'id': row[0],
            'question_group_id': row[1],
            'question': row[2],
            'fill_in_blank_text': row[3],
            'points': row[4],
            'category': row[5],
            'question_type': row[6],
            'options': []
        }

        if question_dict['question_type'] == 'multiple_choice':
            cursor.execute("""
                SELECT id, option_text, is_correct
                FROM question_options
                WHERE question_id = ?;
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

    def get_questions_for_group(self, question_group_id):
        """
        Fetches all questions for a particular group (basic info).
        """
        sql = """
            SELECT id, question
            FROM questions
            WHERE question_group_id = ?;
        """
        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute(sql, (question_group_id,))
        rows = cursor.fetchall()
        conn.close()
        return [{'id': r[0], 'question': r[1]} for r in rows]

    def delete_question(self, question_id):
        """
        Deletes a question and all its options.
        """
        conn = self.create_connection()
        cursor = conn.cursor()

        # Delete options first
        cursor.execute("""
            DELETE FROM question_options
            WHERE question_id = ?;
        """, (question_id,))

        # Then the question itself
        cursor.execute("""
            DELETE FROM questions
            WHERE id = ?;
        """, (question_id,))

        conn.commit()
        conn.close()

    def get_random_question(self, question_group_id, session_id):
        """
        Retrieves a random unanswered question from the specified group.
        """
        conn = self.create_connection()
        cursor = conn.cursor()

        query = """
            SELECT 
                q.id,
                q.question_group_id,
                q.question,
                q.fill_in_blank_text,
                q.points,
                q.category,
                q.question_type
            FROM questions q
            LEFT JOIN session_questions sq ON q.id = sq.question_id AND sq.session_id = ?
            WHERE q.question_group_id = ?
            AND (sq.was_correct IS NULL OR NOT EXISTS (
                SELECT 1 FROM session_questions
                WHERE question_id = q.id AND session_id = ?
            ))
            ORDER BY RANDOM()
            LIMIT 1;
        """
        
        cursor.execute(query, (session_id, question_group_id, session_id))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None

        question_dict = {
            'id': row[0],
            'question_group_id': row[1],
            'question': row[2],
            'fill_in_blank_text': row[3],
            'points': row[4],
            'category': row[5],
            'question_type': row[6],
            'options': []
        }

        # If multiple choice, get the options
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

    def delete_group(self, question_group_id):
        """
        Deletes a group and all associated questions (and their options).
        """
        # 1. Find all questions for this group
        questions = self.get_questions_for_group(question_group_id)

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
            WHERE question_group_id = ?;
        """, (question_group_id,))

        # 4. Delete the group itself
        cursor.execute("""
            DELETE FROM groups
            WHERE id = ?;
        """, (question_group_id,))

        conn.commit()
        conn.close()

    # ----------------------------------------------------------------
    #                          SESSIONS
    # ----------------------------------------------------------------
    def create_session(self, time_per_question, question_group_id):
        """
        Inserts a new session record, storing time_per_question and question_group_id.
        Returns the new session_id.
        """
        sql = """
            INSERT INTO sessions (time_per_question, is_active, question_group_id)
            VALUES (?, 1, ?);
        """
        cursor, conn = self._exec_commit(sql, (time_per_question, question_group_id))
        sid = cursor.lastrowid
        conn.close()
        return sid

    def get_session(self, session_id):
        """
        Retrieves session info by session_id, including question_group_id.
        """
        sql = """
            SELECT
                id, created_at, is_active, time_per_question,
                current_turn_team_id, question_group_id
            FROM sessions
            WHERE id = ?;
        """
        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute(sql, (session_id,))
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
            'question_group_id': row[5]
        }

    def update_session_status(self, session_id, is_active):
        """
        Marks a session active/inactive.
        """
        sql = """
            UPDATE sessions
            SET is_active = ?
            WHERE id = ?;
        """
        self._exec_commit(sql, (1 if is_active else 0, session_id))

    # ----------------------------------------------------------------
    #                        TEAMS + PLAYERS
    # ----------------------------------------------------------------
    def add_team(self, session_id, team_name):
        sql = """
            INSERT INTO teams (session_id, team_name)
            VALUES (?, ?);
        """
        cursor, conn = self._exec_commit(sql, (session_id, team_name))
        team_id = cursor.lastrowid
        conn.close()
        return team_id

    def add_player_to_team(self, team_id, player_name):
        sql = """
            INSERT INTO players (team_id, player_name)
            VALUES (?, ?);
        """
        cursor, conn = self._exec_commit(sql, (team_id, player_name))
        player_id = cursor.lastrowid
        conn.close()
        return player_id

    def get_teams_for_session(self, session_id):
        """
        Returns a list of teams in this session, each with a list of players.
        """
        conn = self.create_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, team_name
            FROM teams
            WHERE session_id = ?;
        """, (session_id,))
        team_rows = cursor.fetchall()

        results = []
        for (team_id, team_name) in team_rows:
            # get players
            cursor.execute("""
                SELECT id, player_name
                FROM players
                WHERE team_id = ?;
            """, (team_id,))
            player_rows = cursor.fetchall()
            players = [
                {'id': p[0], 'player_name': p[1]}
                for p in player_rows
            ]
            results.append({
                'team_id': team_id,
                'team_name': team_name,
                'players': players
            })

        conn.close()
        return results

    # ----------------------------------------------------------------
    #                      GAME STATE TRACKING
    # ----------------------------------------------------------------
    def init_session_state(self, session_id, team_ids):
        """
        Inserts rows into session_state for each team with score=0.
        """
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
        """
        Returns {
          'current_turn_team_id': X,
          'scores': { team_id: score, ... }
        }
        """
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

        scores = {r[0]: r[1] for r in rows}
        conn.close()

        return {
            'current_turn_team_id': current_turn_team_id,
            'scores': scores
        }

    def update_score(self, session_id, team_id, new_score):
        sql = """
            UPDATE session_state
            SET score = ?
            WHERE session_id = ? AND team_id = ?;
        """
        self._exec_commit(sql, (new_score, session_id, team_id))

    def update_current_turn(self, session_id, next_team_id):
        sql = """
            UPDATE sessions
            SET current_turn_team_id = ?
            WHERE id = ?;
        """
        self._exec_commit(sql, (next_team_id, session_id))

    def mark_question_answered(self, session_id, question_id, was_correct):
        """Records that a question was answered in the session."""
        sql = """
            INSERT INTO session_questions 
                (session_id, question_id, was_correct, answered)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(session_id, question_id) 
            DO UPDATE SET 
                was_correct = ?,
                answered = 1,
                answered_at = CURRENT_TIMESTAMP;
        """
        self._exec_commit(sql, (session_id, question_id, was_correct, was_correct))

    def any_questions_left_for_session(self, session_id, question_group_id):
        """
        Returns True if there are any unanswered questions remaining.
        """
        sql = """
            SELECT q.id
            FROM questions q
            WHERE q.question_group_id = ?
            AND NOT EXISTS (
                SELECT 1
                FROM session_questions sq
                WHERE sq.question_id = q.id
                AND sq.session_id = ?
                AND sq.was_correct IS NOT NULL
            )
            LIMIT 1;
        """
        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute(sql, (question_group_id, session_id))
        row = cursor.fetchone()
        conn.close()
        return row is not None

    def create_new_session(self, time_per_question, question_group_id):
        """Creates a new session and initializes session questions."""
        conn = self.create_connection()
        cursor = conn.cursor()
        
        # Create the session
        cursor.execute("""
            INSERT INTO sessions (time_per_question, question_group_id, is_active)
            VALUES (?, ?, 1);
        """, (time_per_question, question_group_id))
        
        session_id = cursor.lastrowid
        
        # Initialize questions for this session
        cursor.execute("""
            INSERT INTO session_questions (session_id, question_id, was_correct, answered)
            SELECT ?, id, NULL, 0
            FROM questions
            WHERE question_group_id = ?;
        """, (session_id, question_group_id))
        
        conn.commit()
        conn.close()
        return session_id