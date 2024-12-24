import re
import random
import string

from db_manager import DBManager


class GameLogic:
    """
    Handles the core mechanics of the quiz-style game, including:
    - Session management (create/resume)
    - Team setup
    - Time-per-question setting
    - Score and turn tracking
    - Single group per session
    """

    def __init__(self):
        self.db = DBManager()
        self.current_session_id = None
        self.current_session_info = None
        self.teams = []
        self.scores = {}

    def start_new_session(self, time_per_question):
        """
        1. Ask the user which group to use
        2. Creates a new session in DB (time_per_question, group_id)
        3. Store session_id so we can do subsequent operations
        """
        group_id = self.prompt_for_group()
        if group_id is None:
            print("[GameLogic] No valid group selected. Cannot start session.")
            return None

        session_id = self.db.create_session(time_per_question, group_id)
        print(f"[GameLogic] New session created with ID: {session_id}")

        self.current_session_id = session_id
        # Load the session info
        self.current_session_info = self.db.get_session(session_id)
        return session_id

    def prompt_for_group(self):
        """
        Lists all groups from the DB, asks user to pick one by ID, returns that ID or None if invalid.
        """
        conn = self.db.create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, group_name FROM groups ORDER BY id ASC;")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            print("[GameLogic] No groups available.")
            return None

        print("\nAvailable Groups:")
        for gid, gname in rows:
            print(f"  {gid} - {gname}")

        choice = input("\nEnter the ID of the group to use for this session: ")
        try:
            chosen_id = int(choice)
        except ValueError:
            print("[GameLogic] Invalid input.")
            return None

        valid_ids = [r[0] for r in rows]
        if chosen_id not in valid_ids:
            print("[GameLogic] That group ID doesn't exist.")
            return None

        return chosen_id

    def resume_session(self, session_id):
        """
        Resume existing session, including which group was chosen initially.
        """
        session_data = self.db.get_session(session_id)
        if not session_data:
            print(f"[GameLogic] No session found for ID {session_id}.")
            return False

        self.current_session_id = session_id
        self.current_session_info = session_data

        print(
            f"[GameLogic] Resuming session {session_id}, is_active={session_data['is_active']}"
        )
        print(f"[GameLogic] This session uses group ID: {session_data['group_id']}")

        self.teams = self.db.get_teams_for_session(session_id)
        state_data = self.db.get_session_state(session_id)
        self.scores = state_data["scores"]

        current_turn_team_id = state_data["current_turn_team_id"]
        if current_turn_team_id:
            self.current_session_info["current_turn_team_id"] = current_turn_team_id

        print(f"[GameLogic] Current scores: {self.scores}")
        print(f"[GameLogic] Current turn: Team ID {current_turn_team_id}")
        return True

    def setup_teams(self, session_id):
        print("\n=== Setup Teams ===")
        while True:
            team_name = input(
                "Enter a team name (or press Enter to finish adding teams): "
            )
            if not team_name.strip():
                break

            team_id = self.db.add_team(session_id, team_name)
            print(f"Team '{team_name}' created with ID {team_id}.")

            add_players = input("Add players to this team? (y/n): ")
            if add_players.lower() == "y":
                while True:
                    player_name = input(
                        "Enter player name (or press Enter to finish): "
                    )
                    if not player_name.strip():
                        break
                    player_id = self.db.add_player_to_team(team_id, player_name)
                    print(f"Player '{player_name}' added (ID {player_id}).")

        # Refresh local teams
        self.teams = self.db.get_teams_for_session(session_id)
        team_ids = [t["team_id"] for t in self.teams]
        self.db.init_session_state(session_id, team_ids)
        print("[GameLogic] Team setup complete. Initial scores set to 0.")

    def set_time_per_question(self, session_id, seconds):
        """
        Allows changing the session's time_per_question mid-game if desired.
        """
        s_data = self.db.get_session(session_id)
        if not s_data:
            print("[GameLogic] Session not found.")
            return
        conn = self.db.create_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE sessions SET time_per_question = ?
            WHERE id = ?;
        """,
            (seconds, session_id),
        )
        conn.commit()
        conn.close()
        self.current_session_info = self.db.get_session(session_id)
        print(
            f"[GameLogic] Updated session {session_id} time_per_question to {seconds}."
        )

    def begin_game_loop(self):
        if not self.current_session_id:
            print("[GameLogic] No active session.")
            return

        session_data = self.db.get_session(self.current_session_id)
        if not session_data or not session_data["is_active"]:
            print("[GameLogic] Session is not active.")
            return

        # If no teams loaded, fetch them
        if not self.teams:
            self.teams = self.db.get_teams_for_session(self.current_session_id)

        # If no current turn, pick the first team as default
        if not session_data["current_turn_team_id"]:
            if self.teams:
                first_tid = self.teams[0]["team_id"]
                self.db.update_current_turn(self.current_session_id, first_tid)
                self.current_session_info["current_turn_team_id"] = first_tid
                print(f"[GameLogic] First turn set to Team ID {first_tid}")

        chosen_group_id = session_data["group_id"]
        if not chosen_group_id:
            print("[GameLogic] No group selected for this session.")
            return

        while True:
            if not self.db.any_questions_left_for_session(
                self.current_session_id, chosen_group_id
            ):
                print("\n[GameLogic] All questions in this group have been answered!")
                break

            s_data = self.db.get_session(self.current_session_id)
            if not s_data["is_active"]:
                print("[GameLogic] Session is inactive. Ending loop.")
                break

            state_data = self.db.get_session_state(self.current_session_id)
            scores = state_data["scores"]
            current_tid = state_data["current_turn_team_id"]

            print("\n=== Current Scores ===")
            for t_id, val in scores.items():
                team = next((x for x in self.teams if x["team_id"] == t_id), None)
                tname = team["team_name"] if team else f"Team {t_id}"
                print(f"  {tname} (ID {t_id}): {val}")

            user_choice = input(
                f"\nTeam ID {current_tid}'s turn. Press Enter to ask a question, or 'Q' to quit: "
            ).strip()
            if user_choice.lower() == "q":
                print("[GameLogic] Quitting loop early; session is still active.")
                break

            q_data = self.db.get_random_question(chosen_group_id)
            if not q_data:
                print("[GameLogic] No more questions found. Ending.")
                break

            was_correct = self.ask_and_evaluate_question(q_data)

            self.db.mark_question_answered(
                self.current_session_id, q_data["id"], was_correct
            )

            old_score = scores.get(current_tid, 0)
            awarded = q_data["points"] if was_correct else 0
            new_score = old_score + awarded
            self.db.update_score(self.current_session_id, current_tid, new_score)
            scores[current_tid] = new_score

            if was_correct:
                print(f"[GameLogic] Correct! +{q_data['points']} points.")
            else:
                print("[GameLogic] Incorrect or skipped—no points awarded.")

            if len(self.teams) > 1:
                all_ids = [t["team_id"] for t in self.teams]
                c_idx = all_ids.index(current_tid)
                n_idx = (c_idx + 1) % len(all_ids)
                next_tid = all_ids[n_idx]
                self.db.update_current_turn(self.current_session_id, next_tid)
                self.current_session_info["current_turn_team_id"] = next_tid
                print(f"[GameLogic] Next turn: Team ID {next_tid}")
            else:
                print("[GameLogic] Only one team—continuing with the same turn.")

        print("[GameLogic] No more questions or user ended loop.")
        self.end_session(self.current_session_id)

    def ask_and_evaluate_question(self, q_data):
        """
        Present the question. Return True if user is correct, else False.
        Uses the question_type to branch logic:
        - multiple_choice
        - fill_in_blank
        - open_ended
        """
        q_type = q_data.get("question_type")
        correct_opt = q_data.get("correct_option")
        question_text = q_data.get("question")

        # 1) MULTIPLE CHOICE
        if q_type == "multiple_choice":
            opts = [
                q_data.get("option1"),
                q_data.get("option2"),
                q_data.get("option3"),
                q_data.get("option4"),
            ]
            valid_opts = [o for o in opts if o]

            print(f"\n[Question] {question_text}")
            print("\nMultiple-choice options:")

            letters = list(string.ascii_uppercase)[: len(valid_opts)]
            for i, opt_text in enumerate(valid_opts):
                print(f"  {letters[i]}) {opt_text}")

            ans = input("Your answer (A/B/C/D or 'skip'): ").upper().strip()
            if ans == "SKIP":
                return False

            # figure out which letter is correct
            correct_index = None
            if correct_opt:
                for i, opt_text in enumerate(valid_opts):
                    if opt_text.strip().lower() == correct_opt.strip().lower():
                        correct_index = i
                        break

            if ans in letters and correct_index is not None:
                return letters.index(ans) == correct_index
            else:
                return False

        # 2) FILL-IN-BLANK
        elif q_type == "fill_in_blank":
            
            if correct_opt:
                
                question_text = re.sub(
                    re.escape(correct_opt),
                    "_____",
                    question_text,
                    flags=re.IGNORECASE,
                )

            print(f"\n[Question] {question_text}")
            ans = input("Your answer (or 'skip'): ").strip()
            if ans.lower() == "skip":
                return False

            if correct_opt:
                return ans.lower() == correct_opt.lower()
            else:
                return False

        # 3) OPEN-ENDED
        elif q_type == "open_ended":
            print(f"\n[Question] {question_text}")
            ans = input("Correct answer? (y/n): ").strip()
            return ans.lower() == "y"

        else:  # unknown
            print(f"\n[Question] {question_text}")
            print("[GameLogic] Unknown question type. Skipping question.")
            return False

    def end_session(self, session_id):
        self.db.update_session_status(session_id, is_active=False)
        final_state = self.db.get_session_state(session_id)
        final_scores = final_state["scores"]

        print("\n=== Final Scores ===")
        high_score = -1
        winners = []

        for t_id, sc in final_scores.items():
            team = next((x for x in self.teams if x["team_id"] == t_id), None)
            t_name = team["team_name"] if team else f"Team {t_id}"
            print(f"  {t_name} (ID {t_id}): {sc}")

            if sc > high_score:
                high_score = sc
                winners = [t_name]
            elif sc == high_score:
                winners.append(t_name)

        if len(winners) == 1:
            print(f"\n[GameLogic] Winner is {winners[0]}!")
        else:
            print(f"\n[GameLogic] It's a tie between {', '.join(winners)}.")

        print(f"[GameLogic] Session {session_id} now closed.")
