from game_logic import GameLogic
from input_questions import create_new_group, list_all_groups, run_question_input


def main():
    game = GameLogic()

    while True:
        print("\n=== Main Menu ===")
        print("1) Manage Question Groups (create, add questions)")
        print("2) Start a new session")
        print("3) Resume an existing session")
        print("4) End a session")
        print("5) Quit")

        choice = input("Choose an option: ")

        if choice == "1":
            manage_groups_menu()

        elif choice == "2":
            time_str = input("Enter time per question (seconds, e.g., 30): ")
            try:
                time_per_q = int(time_str)
            except ValueError:
                time_per_q = 30

            session_id = game.start_new_session(time_per_q)

            game.setup_teams(session_id)

            print("\n>>> Starting Game Loop...")
            game.begin_game_loop()

        elif choice == "3":
            sess_str = input("Enter the session ID to resume: ")
            try:
                sess_id = int(sess_str)
            except ValueError:
                print("Invalid session ID. Returning to main menu.")
                continue

            success = game.resume_session(sess_id)
            if success:
                print("\n>>> Starting Game Loop...")
                game.begin_game_loop()

        elif choice == "4":
            sess_str = input("Enter the session ID to end: ")
            try:
                sess_id = int(sess_str)
            except ValueError:
                print("Invalid session ID. Returning to main menu.")
                continue

            game.end_session(sess_id)

        elif choice == "5":
            print("Exiting application. Goodbye!")
            break

        else:
            print("Invalid choice. Please try again.")


def manage_groups_menu():
    """
    Sub-menu to create new groups, list all groups,
    and add questions to a chosen group.
    """
    while True:
        print("\n=== Group Management Menu ===")
        print("1) Create a new group")
        print("2) List all groups")
        print("3) Add questions to a group")
        print("4) Return to main menu")

        choice = input("Choose an option: ")
        if choice == "1":
            create_new_group()

        elif choice == "2":
            list_all_groups()

        elif choice == "3":
            run_question_input()

        elif choice == "4":
            print("Returning to main menu.")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
