
from db_manager import DBManager

def prompt_for_group_name():
    """
    Asks the user for a group name (e.g., 'Math Trivia').
    Returns the group_name string.
    """
    group_name = input("Enter a name for the new group: ")
    return group_name.strip()

def prompt_question_type():
    """
    Prompts the user to choose from the 3 question types:
      1) Multiple Choice
      2) Fill in the Blank
      3) Open Ended
    Returns a string: 'multiple_choice', 'fill_in_blank', or 'open_ended'.
    """
    print("\nSelect a question type:")
    print("1) Multiple Choice")
    print("2) Fill in the Blank")
    print("3) Open Ended")
    choice = input("Enter choice (1/2/3): ").strip()
    if choice == '1':
        return 'multiple_choice'
    elif choice == '2':
        return 'fill_in_blank'
    elif choice == '3':
        return 'open_ended'
    else:
        print("Invalid choice, defaulting to 'open_ended'.")
        return 'open_ended'

def create_new_group():
    """
    Interactively prompts the user for a group name, 
    creates the group in the DB, then immediately starts adding questions.
    """
    db = DBManager()
    group_name = prompt_for_group_name()
    new_group_id = db.insert_group(group_name)
    print(f"\nGroup '{group_name}' created with ID {new_group_id}.")

    add_questions_loop(new_group_id)

def list_all_groups():
    """
    Fetches all groups from DB and displays them.
    """
    db = DBManager()
    conn = db.create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, group_name 
        FROM groups
        ORDER BY id ASC;
    """)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("No groups found.")
    else:
        print("\nExisting Groups:")
        for row in rows:
            print(f"  ID: {row[0]} | Name: {row[1]}")

def prompt_new_question(group_id):
    """
    Interactively asks which question type the user wants to create,
    then gathers question text and other details based on that type.
    Returns a dict that can be inserted by DBManager (including question_type).
    """

    q_type = prompt_question_type()

    question_text = input("\nEnter the question text: ").strip()

    option1 = None
    option2 = None
    option3 = None
    option4 = None
    correct_option = None

    if q_type == 'multiple_choice':
        print("\nEnter up to 4 choices (leave blank if fewer than 4).")
        choice1 = input("Choice 1: ").strip()
        choice2 = input("Choice 2: ").strip()
        choice3 = input("Choice 3: ").strip()
        choice4 = input("Choice 4: ").strip()

        option1 = choice1 or None
        option2 = choice2 or None
        option3 = choice3 or None
        option4 = choice4 or None

        print("\nWhich choice is correct? (1/2/3/4) or leave blank if none.")
        correct_idx = input("Correct choice number: ").strip()
        if correct_idx in ["1", "2", "3", "4"]:
            if correct_idx == "1" and choice1:
                correct_option = choice1
            elif correct_idx == "2" and choice2:
                correct_option = choice2
            elif correct_idx == "3" and choice3:
                correct_option = choice3
            elif correct_idx == "4" and choice4:
                correct_option = choice4

    elif q_type == 'fill_in_blank':
        print("\nFill-in-the-Blank: Enter the correct text (exact match).")
        correct_option = input("Correct text: ").strip()

    else:  # 'open_ended'
        print("\nOpen-Ended: Optionally provide a 'model' answer or press Enter.")
        possible_answer = input("Model answer (optional): ").strip()
        if possible_answer:
            correct_option = possible_answer

    points_str = input("\nPoints for this question (default = 10): ").strip()
    category = input("Category (optional): ").strip()

    try:
        points = int(points_str) if points_str else 10
    except ValueError:
        points = 10

    question_data = {
        'group_id': group_id,
        'question': question_text,
        'option1': option1,
        'option2': option2,
        'option3': option3,
        'option4': option4,
        'correct_option': correct_option,
        'points': points,
        'category': category if category else None,
        'question_type': q_type
    }

    return question_data


def add_questions_loop(group_id):
    """
    Keeps asking the user if they want to add more questions
    to the specified group_id. Ends when user says 'no'.
    """
    db = DBManager()
    while True:
        question_data = prompt_new_question(group_id)
        q_id = db.insert_question(question_data)
        print(f"Question inserted with ID {q_id}.")

        another = input("Add another question to this group? (y/n): ").lower()
        if another != 'y':
            print(f"\nDone adding questions to group ID {group_id}.")
            break

def run_question_input():
    """
    A loop that lets the user select a group (or create one),
    then add multiple questions to that group until done.
    """
    db = DBManager()

    while True:
        print("\n---- Question Management Menu ----")
        print("1. Create a new group (and add questions)")
        print("2. List all groups")
        print("3. Select a group to add questions")
        print("4. Quit")
        choice = input("\nEnter your choice: ").strip()

        if choice == '1':
            create_new_group()

        elif choice == '2':
            list_all_groups()

        elif choice == '3':
            list_all_groups()
            group_id_str = input("Enter the group ID to which you want to add questions: ")
            try:
                group_id = int(group_id_str)
            except ValueError:
                print("Invalid ID. Returning to main menu.")
                continue

            conn = db.create_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM groups WHERE id = ?;", (group_id,))
            row = cursor.fetchone()
            conn.close()

            if not row:
                print(f"Group ID {group_id} does not exist.")
                continue

            add_questions_loop(group_id)

        elif choice == '4':
            print("Exiting Question Management.")
            break

        else:
            print("Invalid selection. Please try again.")

def main():
    """
    Main entry point for this script:
    1. Initialize DB + create tables
    2. Provide a menu to create groups or add questions
    """
    print("Welcome to the Question Input Script!")
    run_question_input()

if __name__ == "__main__":
    main()
