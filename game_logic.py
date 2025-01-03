from db_manager import DBManager

class GameLogic:
    """
    Handles the core mechanics of the quiz-style game, including:
    - Session creation
    - Team setup
    - Score and turn tracking
    - Single group per session
    - Marking questions answered
    - Retrieving random questions
    - Ending sessions
    """

    def __init__(self, db=None):
        # If no db passed, create a default one
        self.db = db if db else DBManager()
        self.current_session_id = None
        self.current_session_info = None
        self.teams = []
        self.scores = {}

    def create_new_session(self, time_per_question, question_group_id):
        """
        Creates a brand-new session in the DB, storing question_group_id and time_per_question,
        ensuring we do not accidentally reuse or conflict with an old session.
        """
        # If there was an old session still active, end it
        if self.current_session_id is not None:
            self.end_session()

        # Create new session and initialize questions
        self.current_session_id = self.db.create_new_session(time_per_question, question_group_id)
        self.current_session_info = self.db.get_session(self.current_session_id)

        # Clear local team references
        self.teams = []
        self.scores = {}

        return self.current_session_id


    def load_session(self, session_id):
        """
        Load an existing session.
        """
        s_data = self.db.get_session(session_id)
        if not s_data:
            return False

        self.current_session_id = session_id
        self.current_session_info = s_data
        # Load teams, scores, etc.
        self.teams = self.db.get_teams_for_session(session_id)
        state_data = self.db.get_session_state(session_id)
        self.scores = state_data["scores"]
        return True

    def setup_teams(self, team_names):
        if not self.current_session_id:
            return

        # Insert teams
        for name in team_names:
            self.db.add_team(self.current_session_id, name)

        # Re-fetch teams and init state
        self.teams = self.db.get_teams_for_session(self.current_session_id)
        team_ids = [t["team_id"] for t in self.teams]
        self.db.init_session_state(self.current_session_id, team_ids)

        # Now check if there's a current_turn_team_id
        state_data = self.db.get_session_state(self.current_session_id)
        if not state_data["current_turn_team_id"] and team_ids:
            # Set the turn to the first team
            self.db.update_current_turn(self.current_session_id, team_ids[0])
            # Optionally update your local self.current_session_info as well
            self.current_session_info["current_turn_team_id"] = team_ids[0]


    def begin_game_loop(self):
        """
        Get a random question if any remain. Return the question dict or None if no questions left.
        """
        if not self.current_session_id:
            print("[DEBUG] No current session ID")
            return None
            
        s_data = self.db.get_session(self.current_session_id)
        if not s_data or not s_data["is_active"]:
            print("[DEBUG] Session not found or not active")
            return None

        question_group_id = s_data["question_group_id"]
        if not question_group_id:
            print("[DEBUG] No question group ID found")
            return None

        print(f"[DEBUG] Checking for questions in group {question_group_id}")
        any_left = self.db.any_questions_left_for_session(self.current_session_id, question_group_id)
        print(f"[DEBUG] Questions remaining: {any_left}")

        if not any_left:
            print("[DEBUG] No questions remain")
            return None

        # Fetch a random question
        question = self.db.get_random_question(question_group_id, self.current_session_id)
        print(f"[DEBUG] Got random question: {question}")
        return question


    def mark_answer(self, question_id, was_correct, points=0):
        """
        Mark a question as answered, update score if correct, rotate turn to the next team.
        """
        if not self.current_session_id:
            return

        # Mark question answered
        self.db.mark_question_answered(self.current_session_id, question_id, was_correct)

        # Update scores
        state_data = self.db.get_session_state(self.current_session_id)
        current_tid = state_data["current_turn_team_id"]
        old_score = state_data["scores"].get(current_tid, 0)
        new_score = old_score + (points if was_correct else 0)
        self.db.update_score(self.current_session_id, current_tid, new_score)

        # Rotate turn if multiple teams
        if len(state_data["scores"]) > 1:
            all_ids = list(state_data["scores"].keys())  # team IDs
            c_idx = all_ids.index(current_tid)
            n_idx = (c_idx + 1) % len(all_ids)
            next_tid = all_ids[n_idx]
            self.db.update_current_turn(self.current_session_id, next_tid)

    def get_current_team_id(self):
        """
        Return the ID of the team whose turn it is.
        """
        st = self.db.get_session_state(self.current_session_id)
        return st["current_turn_team_id"]

    def get_scores(self):
        """
        Return a dict of { team_id: score }
        """
        return self.db.get_session_state(self.current_session_id)["scores"]

    def end_session(self):
        """
        Mark the current session inactive.
        """
        if self.current_session_id:
            self.db.update_session_status(self.current_session_id, False)
            self.current_session_id = None
            self.current_session_info = None
            self.teams = []
            self.scores = {}
