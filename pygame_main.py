import pygame
import re
from db_manager import DBManager
from game_logic import GameLogic
from display_manager import DisplayManager
from responsive_layout import ResponsiveLayout

pygame.init()

# Initialize Display Manager
display_manager = DisplayManager()

# We'll now create a function to get scaled fonts instead of global font objects
def get_font(size):
    """Get a properly scaled font of the specified base size."""
    return display_manager.get_scaled_font(size)


# ---------------------------
# Game States
# ---------------------------
MAIN_MENU = "MAIN_MENU"
MANAGE_GROUPS = "MANAGE_GROUPS"
ADD_GROUP = "ADD_GROUP"
SELECT_GROUP = "SELECT_GROUP"
VIEW_GROUP = "VIEW_GROUP"
SELECT_QUESTION_TYPE = "SELECT_QUESTION_TYPE"
ADD_QUESTIONS = "ADD_QUESTIONS"

SESSION_SETUP = "SESSION_SETUP"
TEAM_SETUP = "TEAM_SETUP"
GAMEPLAY = "GAMEPLAY"
FEEDBACK = "FEEDBACK"

current_state = MAIN_MENU

# ---------------------------
# Database + Game Logic
# ---------------------------
db = DBManager()
game_logic = GameLogic(db)

# ---------------------------
# Shared Variables
# ---------------------------
focused_field = None
selected_question_group_id = None
selected_question_type = None
question_data = {}  # Holds question info (including editing vs. new)
input_text = ""  # For add_group screen

session_setup_data = {
    "question_group_id": None,
    "time_per_question": "30",
}
team_list = []  # list of team names user adds
team_input_text = ""  # used to type new team name


# ---------------------------
# Core Helper Functions
# ---------------------------

def get_team_name(team_id):
    """
    A small helper that returns the team name from game_logic.teams
    or a fallback if not found.
    """
    for t in game_logic.teams:
        if t["team_id"] == team_id:
            return t["team_name"]
    return f"Team {team_id}"


# ---------------------------
# Draw Screens
# ---------------------------
def draw_main_menu(display_manager):
    """Draw the main menu screen with responsive elements."""
    # Initialize responsive layout
    layout = ResponsiveLayout(display_manager)
    
    # Clear screen
    display_manager.screen.fill((255, 255, 255))  # white background
    
    # Draw title
    layout.draw_text_centered(0.1, "Clynboozle", size_multiplier=1.5)
    
    # Create main menu buttons
    start_game_btn = layout.create_centered_button(
        y_percent=0.3,        # 30% down from top
        width_percent=0.4,    # 40% of screen width
        height_percent=0.1,   # 10% of screen height
        color=(0, 0, 255),    # blue
        text="Start Game"
    )
    
    manage_groups_btn = layout.create_centered_button(
        y_percent=0.45,
        width_percent=0.4,
        height_percent=0.1,
        color=(0, 0, 255),
        text="Manage Groups"
    )
    
    quit_btn = layout.create_centered_button(
        y_percent=0.6,
        width_percent=0.4,
        height_percent=0.1,
        color=(0, 0, 255),
        text="Quit"
    )
    
    return start_game_btn, manage_groups_btn, quit_btn

def draw_manage_groups(display_manager):
    """Draw the manage groups screen with responsive elements."""
    layout = ResponsiveLayout(display_manager)
    display_manager.screen.fill('white')
    
    # Title
    layout.draw_text_centered(0.08, "Manage Groups", size_multiplier=1.5)
    
    # Main buttons
    back_btn = layout.create_positioned_button(
        x_percent=0.05,
        y_percent=0.85,
        width_percent=0.15,
        height_percent=0.08,
        color=(0, 0, 255),
        text="Back"
    )
    
    add_group_btn = layout.create_centered_button(
        y_percent=0.3,
        width_percent=0.3,
        height_percent=0.1,
        color=(0, 0, 255),
        text="Add Group"
    )
    
    select_group_btn = layout.create_centered_button(
        y_percent=0.45,
        width_percent=0.3,
        height_percent=0.1,
        color=(0, 0, 255),
        text="View Groups"
    )
    
    return back_btn, add_group_btn, select_group_btn


def draw_select_group(display_manager):
    """Draw the group selection screen with responsive elements."""
    layout = ResponsiveLayout(display_manager)
    display_manager.screen.fill('white')
    
    # Title
    layout.draw_text_centered(0.08, "Select a Group", size_multiplier=1.5)
    
    # Back button
    back_btn = layout.create_centered_button(
        y_percent=0.85,
        width_percent=0.15,
        height_percent=0.08,
        color=(0, 0, 255),
        text="Back"
    )
    
    # Get groups from database
    conn = db.create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, group_name FROM groups")
    groups = cursor.fetchall()
    conn.close()
    
    # Create grid of group buttons
    buttons = layout.create_grid_buttons(
        items=[f"{g[0]}: {g[1]}" for g in groups],
        start_y_percent=0.2,
        button_width_percent=0.4,
        button_height_percent=0.08,
        color=(0, 0, 255)
    )
    
    # Convert buttons to expected format
    group_buttons = [(btn, gid) for (btn, _), (gid, _) in zip(buttons, groups)]
    
    return back_btn, group_buttons

def draw_add_group(display_manager, input_text):
    """Draw the add group screen with responsive elements."""
    layout = ResponsiveLayout(display_manager)
    display_manager.screen.fill('white')
    
    # Headers
    layout.draw_text_centered(0.08, "Add New Group", size_multiplier=1.5)
    layout.draw_text_centered(0.18, "Create a New Question Group", size_multiplier=1.2)
    
    # Input field with label
    input_box = layout.create_input_field(
        y_percent=0.3,
        width_percent=0.6,
        height_percent=0.08,
        text=input_text,
        label="Group Name:"
    )
    
    # Helper text
    layout.draw_text_centered(
        0.42,
        "Enter a descriptive name for your question group",
        size_multiplier=0.75,
        color=(128, 128, 128)
    )
    
    # Buttons
    back_btn = layout.create_centered_button(
        y_percent=0.85,
        width_percent=0.15,
        height_percent=0.08,
        color=(0, 0, 255),
        text="Back"
    )
    
    save_btn = layout.create_centered_button(
        y_percent=0.7,
        width_percent=0.3,
        height_percent=0.08,
        color=(0, 0, 255) if input_text else (128, 128, 128),
        text="Save"
    )
    
    return back_btn, input_box, save_btn

def draw_view_group(display_manager, question_group_id):
    """Draw the question group view screen with responsive elements."""
    layout = ResponsiveLayout(display_manager)
    display_manager.screen.fill('white')
    
    # Title
    layout.draw_text_centered(0.08, f"Group {question_group_id} Questions", size_multiplier=1.5)
    
    # Navigation buttons
    back_btn = layout.create_positioned_button(
        x_percent=0.05,
        y_percent=0.85,
        width_percent=0.15,
        height_percent=0.08,
        color=(0, 0, 255),
        text="Back"
    )
    
    add_question_btn = layout.create_positioned_button(
        x_percent=0.25,
        y_percent=0.85,
        width_percent=0.2,
        height_percent=0.08,
        color=(0, 0, 255),
        text="Add Question"
    )
    
    delete_group_btn = layout.create_positioned_button(
        x_percent=0.75,
        y_percent=0.85,
        width_percent=0.2,
        height_percent=0.08,
        color=(255, 0, 0),
        text="Delete Group"
    )
    
    # Question list
    questions = db.get_questions_for_group(question_group_id)
    question_buttons = []
    current_y = 0.2  # Start at 20% of screen height
    
    for q in questions:
        # Question button
        q_btn = layout.create_positioned_button(
            x_percent=0.05,
            y_percent=current_y,
            width_percent=0.7,
            height_percent=0.08,
            color=(128, 128, 128),
            text=q['question']
        )
        
        # Delete button
        del_btn = layout.create_positioned_button(
            x_percent=0.8,
            y_percent=current_y,
            width_percent=0.15,
            height_percent=0.08,
            color=(255, 0, 0),
            text="Delete"
        )
        
        question_buttons.append((q_btn, del_btn, q['id']))
        current_y += 0.1  # Move down 10% of screen height
    
    return back_btn, add_question_btn, delete_group_btn, question_buttons

def draw_select_question_type(display_manager):
    """Draw the question type selection screen with responsive elements."""
    layout = ResponsiveLayout(display_manager)
    display_manager.screen.fill('white')
    
    # Title
    layout.draw_text_centered(0.08, "Select Question Type", size_multiplier=1.5)
    
    # Question type buttons
    buttons = []
    button_configs = [
        ("Multiple Choice", 0.3),
        ("Fill in the Blank", 0.45),
        ("Open Ended", 0.6)
    ]
    
    for text, y_pos in button_configs:
        btn = layout.create_centered_button(
            y_percent=y_pos,
            width_percent=0.4,
            height_percent=0.1,
            color=(0, 0, 255),
            text=text
        )
        buttons.append(btn)
    
    back_btn = layout.create_positioned_button(
        x_percent=0.05,
        y_percent=0.85,
        width_percent=0.15,
        height_percent=0.08,
        color=(0, 0, 255),
        text="Back"
    )
    
    return (back_btn, *buttons)


def draw_add_questions(display_manager):
    """Draw the question addition screen with responsive elements."""
    layout = ResponsiveLayout(display_manager)
    display_manager.screen.fill('white')
    
    # Title
    layout.draw_text_centered(0.08, "Add Question Details", size_multiplier=1.5)
    
    # Question input field
    question_box = layout.create_input_field(
        y_percent=0.2,
        width_percent=0.7,
        height_percent=0.06,
        text=question_data.get("question", ""),
        label="Question:"
    )
    
    input_fields = [("question", question_box)]
    current_y = 0.3
    add_choice_btn = None
    
    # Handle different question types
    if question_data.get("question_type") == "multiple_choice":
        options = question_data.get("options", [])
        for i, opt in enumerate(options):
            # Option input
            option_box = layout.create_input_field(
                y_percent=current_y,
                width_percent=0.5,
                height_percent=0.06,
                text=opt["text"],
                label=f"Option {i+1}:"
            )
            input_fields.append((f"option_{i}", option_box))
            
            # Correct/incorrect toggle
            toggle_btn = layout.create_positioned_button(
                x_percent=0.8,
                y_percent=current_y,
                width_percent=0.05,
                height_percent=0.06,
                color=(0, 255, 0) if opt.get("is_correct") else (255, 0, 0),
                text=""
            )
            input_fields.append((f"toggle_correct_{i}", toggle_btn))
            
            current_y += 0.08
        
        add_choice_btn = layout.create_positioned_button(
            x_percent=0.05,
            y_percent=current_y,
            width_percent=0.2,
            height_percent=0.06,
            color=(0, 0, 255),
            text="Add Choice"
        )
        current_y += 0.08
    
    elif question_data.get("question_type") == "fill_in_blank":
        blank_box = layout.create_input_field(
            y_percent=current_y,
            width_percent=0.4,
            height_percent=0.06,
            text=str(question_data.get("blank_text", "")),
            label="Fill-in text:"
        )
        input_fields.append(("blank_text", blank_box))
        current_y += 0.08
    
    # Points field
    points_box = layout.create_input_field(
        y_percent=current_y,
        width_percent=0.15,
        height_percent=0.06,
        text=str(question_data.get("points", "10")),
        label="Points:"
    )
    input_fields.append(("points", points_box))
    current_y += 0.08
    
    # Category field
    category_box = layout.create_input_field(
        y_percent=current_y,
        width_percent=0.4,
        height_percent=0.06,
        text=str(question_data.get("category", "")),
        label="Category:"
    )
    input_fields.append(("category", category_box))
    
    # Buttons
    back_btn = layout.create_positioned_button(
        x_percent=0.05,
        y_percent=0.85,
        width_percent=0.15,
        height_percent=0.08,
        color=(0, 0, 255),
        text="Back"
    )
    
    save_btn = layout.create_centered_button(
        y_percent=0.85,
        width_percent=0.3,
        height_percent=0.08,
        color=(0, 0, 255),
        text="Update" if question_data.get("is_edit") else "Save"
    )
    
    return back_btn, input_fields, add_choice_btn, save_btn

# ---------------------------
# GAME LOGIC
# ---------------------------
def draw_session_setup(display_manager):
    """Draw the game session setup screen with responsive elements."""
    layout = ResponsiveLayout(display_manager)
    display_manager.screen.fill('white')
    
    # Title
    layout.draw_text_centered(0.08, "Session Setup", size_multiplier=1.5)
    
    # Get groups from database
    conn = db.create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, group_name FROM groups ORDER BY id ASC;")
    groups = cursor.fetchall()
    conn.close()
    
    # Create grid of group buttons
    group_buttons = []
    current_y = 0.2
    for gid, gname in groups:
        btn = layout.create_centered_button(
            y_percent=current_y,
            width_percent=0.7,
            height_percent=0.08,
            color=(0, 200, 200),
            text=f"{gid}: {gname}"
        )
        group_buttons.append((btn, gid))  # Store only the ID
        current_y += 0.1
    
    # Time input
    time_box = layout.create_input_field(
        y_percent=0.6,
        width_percent=0.15,
        height_percent=0.06,
        text=session_setup_data["time_per_question"],
        label="Time per Question (sec):"
    )
    
    # Create session button
    create_session_btn = layout.create_centered_button(
        y_percent=0.75,
        width_percent=0.3,
        height_percent=0.08,
        color=(0, 0, 255),
        text="Create Session"
    )
    
    back_btn = layout.create_positioned_button(
        x_percent=0.05,
        y_percent=0.85,
        width_percent=0.15,
        height_percent=0.08,
        color=(0, 0, 255),
        text="Back"
    )
    
    return back_btn, group_buttons, time_box, create_session_btn

def draw_team_setup(display_manager):
    """Draw the team setup screen with responsive elements."""
    layout = ResponsiveLayout(display_manager)
    display_manager.screen.fill('white')
    
    # Title
    layout.draw_text_centered(0.08, "Team Setup", size_multiplier=1.5)
    
    # Current teams list
    layout.draw_text_centered(0.18, "Current Teams:", size_multiplier=0.8)
    
    current_y = 0.25
    for team_name in team_list:
        layout.draw_text_centered(current_y, f"- {team_name}", size_multiplier=0.8)
        current_y += 0.05
    
    # Team input
    team_box = layout.create_input_field(
        y_percent=current_y + 0.05,
        width_percent=0.4,
        height_percent=0.06,
        text=team_input_text,
        label="Add Team Name:"
    )
    
    # Buttons
    add_team_btn = layout.create_positioned_button(
        x_percent=0.1,
        y_percent=0.85,
        width_percent=0.2,
        height_percent=0.08,
        color=(0, 0, 255),
        text="Add Team"
    )
    
    done_btn = layout.create_positioned_button(
        x_percent=0.35,
        y_percent=0.85,
        width_percent=0.2,
        height_percent=0.08,
        color=(0, 255, 0),
        text="Done"
    )
    
    back_btn = layout.create_positioned_button(
        x_percent=0.6,
        y_percent=0.85,
        width_percent=0.2,
        height_percent=0.08,
        color=(0, 0, 255),
        text="Back"
    )
    
    return back_btn, team_box, add_team_btn, done_btn

def draw_gameplay(display_manager):
    """Draw the main gameplay screen with responsive elements."""
    layout = ResponsiveLayout(display_manager)
    display_manager.screen.fill('white')
    
    # Check for active session
    if not game_logic.current_session_id:
        layout.draw_text_centered(0.08, "No Active Session!", size_multiplier=1.2, color=(255, 0, 0))
        end_btn = layout.create_centered_button(
            y_percent=0.85,
            width_percent=0.3,
            height_percent=0.08,
            color=(255, 0, 0),
            text="Back to Menu"
        )
        return end_btn, None, None, None
    
    s_data = db.get_session(game_logic.current_session_id)
    if not s_data or not s_data["is_active"]:
        layout.draw_text_centered(0.08, "Session is not active!", size_multiplier=1.2, color=(255, 0, 0))
        end_btn = layout.create_centered_button(
            y_percent=0.85,
            width_percent=0.3,
            height_percent=0.08,
            color=(255, 0, 0),
            text="Back to Menu"
        )
        return end_btn, None, None, None
    
    # Question handling
    if "active_question" not in question_data or question_data["active_question"] is None:
        print(f"[DEBUG] Loading new question for session {game_logic.current_session_id}")
        # Check if any questions are available
        available = db.any_questions_left_for_session(game_logic.current_session_id, s_data['question_group_id'])
        if not available:
            print("[DEBUG] No questions available")
            question_data["active_question"] = None
        else:
            print("[DEBUG] Getting next question")
            q = game_logic.begin_game_loop()
            question_data["active_question"] = q
            question_data["user_answer"] = ""
            print(f"[DEBUG] Loaded question: {q['question'] if q else 'None'}")
    
    aq = question_data.get("active_question")
    if aq is None:
        if not db.any_questions_left_for_session(game_logic.current_session_id, s_data['question_group_id']):
            end_btn = draw_final_scores(display_manager)
            return end_btn, None, None, None
    
    # Display question
    qtype = aq["question_type"]
    q_text = aq["question"]
    
    if qtype == "fill_in_blank" and aq.get("fill_in_blank_text"):
        pat = re.escape(aq["fill_in_blank_text"])
        q_text = re.sub(pat, "_____", q_text, flags=re.IGNORECASE)
    
    layout.draw_text_centered(0.1, q_text, size_multiplier=1.2)
    
    # End session button
    end_btn = layout.create_positioned_button(
        x_percent=0.05,
        y_percent=0.85,
        width_percent=0.2,
        height_percent=0.08,
        color=(255, 0, 0),
        text="End Session"
    )
    
    clickable_buttons = []
    current_y = 0.2
    
    # Handle different question types
    if qtype == "multiple_choice":
        options = aq.get("options", [])
        for i, opt in enumerate(options):
            btn = layout.create_centered_button(
                y_percent=current_y,
                width_percent=0.7,
                height_percent=0.08,
                color=(0, 0, 255),
                text=opt["text"]
            )
            clickable_buttons.append(("MC_OPTION", i, btn))
            current_y += 0.1
    
    elif qtype == "fill_in_blank":
        ans_box = layout.create_input_field(
            y_percent=current_y,
            width_percent=0.4,
            height_percent=0.06,
            text=question_data.get("user_answer", ""),
            label="Your Answer:"
        )
        
        submit_btn = layout.create_positioned_button(
            x_percent=0.7,
            y_percent=current_y,
            width_percent=0.15,
            height_percent=0.06,
            color=(0, 255, 0),
            text="Submit"
        )
        
        clickable_buttons.extend([
            ("FILL_SUBMIT", None, submit_btn),
            ("FILL_BOX", None, ans_box)
        ])
    
    elif qtype == "open_ended":
        correct_btn = layout.create_positioned_button(
            x_percent=0.1,
            y_percent=current_y,
            width_percent=0.25,
            height_percent=0.08,
            color=(0, 255, 0),
            text="Mark Correct"
        )
        
        wrong_btn = layout.create_positioned_button(
            x_percent=0.4,
            y_percent=current_y,
            width_percent=0.25,
            height_percent=0.08,
            color=(255, 0, 0),
            text="Mark Wrong"
        )
        
        clickable_buttons.extend([
            ("OPEN_CORRECT", None, correct_btn),
            ("OPEN_WRONG", None, wrong_btn)
        ])
    
    # Display scores
    current_y = 0.5
    layout.draw_text_centered(current_y, "Scores:", size_multiplier=0.8)
    current_y += 0.05
    
    scores = game_logic.get_scores()
    for tid, sc in scores.items():
        team_name = get_team_name(tid)
        layout.draw_text_centered(current_y, f"{team_name}: {sc}", size_multiplier=0.8)
        current_y += 0.05
    
    return end_btn, None, clickable_buttons, None

def draw_final_scores(display_manager):
    """Draw the final scores screen with responsive elements."""
    layout = ResponsiveLayout(display_manager)
    display_manager.screen.fill('white')
    
    # Title
    layout.draw_text_centered(0.08, "No more questions left!", size_multiplier=1.2, color=(255, 0, 0))
    
    # Get scores and calculate winners
    final_scores = game_logic.get_scores()
    if final_scores:
        max_score = max(final_scores.values())
        winner_ids = [tid for tid, sc in final_scores.items() if sc == max_score]
    else:
        max_score = 0
        winner_ids = []
    
    # Display scores
    layout.draw_text_centered(0.2, "Final Scores:", size_multiplier=1.1)
    current_y = 0.3
    
    for tid, sc in final_scores.items():
        team_name = get_team_name(tid)
        layout.draw_text_centered(current_y, f"{team_name}: {sc}", size_multiplier=0.8)
        current_y += 0.05
    
    # Display winner message
    winner_names = [get_team_name(w_id) for w_id in winner_ids]
    if len(winner_names) == 1:
        winner_msg = f"{winner_names[0]} is the WINNER!"
    elif len(winner_names) > 1:
        winner_msg = f"{', '.join(winner_names)} are the WINNERS!"
    else:
        winner_msg = "No winners?"
    
    layout.draw_text_centered(current_y + 0.05, winner_msg, size_multiplier=1.2, color=(0, 255, 0))
    
    # End button
    end_btn = layout.create_centered_button(
        y_percent=0.85,
        width_percent=0.3,
        height_percent=0.08,
        color=(255, 0, 0),
        text="End Session"
    )
    
    return end_btn

def draw_feedback(display_manager):
    """Draw the feedback screen with responsive elements."""
    layout = ResponsiveLayout(display_manager)
    display_manager.screen.fill('white')
    
    # Title
    layout.draw_text_centered(0.08, "Result", size_multiplier=1.5)
    
    # Result message
    was_correct = question_data.get("last_was_correct", False)
    if was_correct:
        msg_text = f"Correct! +{question_data.get('last_points', 0)} points!"
        msg_color = (0, 255, 0)  # Green
    else:
        msg_text = "Incorrect!"
        msg_color = (255, 0, 0)  # Red
    
    layout.draw_text_centered(0.25, msg_text, size_multiplier=1.2, color=msg_color)
    
    # Control buttons
    next_btn = layout.create_centered_button(
        y_percent=0.5,
        width_percent=0.3,
        height_percent=0.08,
        color=(0, 0, 255),
        text="Next Question"
    )
    
    end_btn = layout.create_centered_button(
        y_percent=0.65,
        width_percent=0.3,
        height_percent=0.08,
        color=(255, 0, 0),
        text="End Session"
    )
    
    return next_btn, end_btn


# ---------------------------
# Event Handlers
# ---------------------------
def handle_main_menu(event, buttons):
    global current_state
    start_game_btn, manage_groups_btn, quit_btn = buttons
    if start_game_btn.collidepoint(event.pos):
        current_state = SESSION_SETUP
    elif manage_groups_btn.collidepoint(event.pos):
        current_state = MANAGE_GROUPS
    elif quit_btn.collidepoint(event.pos):
        pygame.quit()
        exit()


def handle_manage_groups(event, buttons):
    global current_state
    back_btn, add_group_btn, select_group_btn = buttons
    if back_btn.collidepoint(event.pos):
        current_state = MAIN_MENU
    elif add_group_btn.collidepoint(event.pos):
        current_state = ADD_GROUP
    elif select_group_btn.collidepoint(event.pos):
        current_state = SELECT_GROUP


def handle_add_group(event, buttons):
    global current_state, input_text
    back_btn, input_box, save_btn = buttons
    if back_btn.collidepoint(event.pos):
        current_state = MANAGE_GROUPS
    elif save_btn.collidepoint(event.pos) and input_text:
        db.insert_group(input_text)
        input_text = ""
        current_state = MANAGE_GROUPS


def handle_select_group(event, buttons):
    global current_state, selected_question_group_id
    back_btn, group_buttons = buttons
    if back_btn.collidepoint(event.pos):
        current_state = MANAGE_GROUPS
    else:
        for group_btn, g_id in group_buttons:
            if group_btn.collidepoint(event.pos):
                selected_question_group_id = g_id
                current_state = VIEW_GROUP


def handle_view_group(event, buttons):
    global current_state, question_data
    back_btn, add_question_btn, delete_group_btn, question_buttons = buttons
    if back_btn.collidepoint(event.pos):
        current_state = SELECT_GROUP
    elif add_question_btn.collidepoint(event.pos):
        current_state = SELECT_QUESTION_TYPE
    elif delete_group_btn.collidepoint(event.pos):
        db.delete_group(selected_question_group_id)
        current_state = SELECT_GROUP
    else:
        for q_btn, del_btn, q_id in question_buttons:
            if q_btn.collidepoint(event.pos):
                existing_q = db.get_question(q_id)
                if existing_q:
                    question_data.clear()
                    question_data["is_edit"] = True
                    question_data["question_id"] = existing_q["id"]
                    question_data["question"] = existing_q["question"]
                    question_data["points"] = existing_q["points"]
                    question_data["category"] = existing_q["category"]
                    question_data["question_type"] = existing_q["question_type"]
                    if existing_q["question_type"] == "multiple_choice":
                        question_data["options"] = existing_q.get("options", [])
                    elif existing_q["question_type"] == "fill_in_blank":
                        question_data["blank_text"] = existing_q.get(
                            "fill_in_blank_text", ""
                        )
                    current_state = ADD_QUESTIONS
                else:
                    print(f"Question ID {q_id} not found in DB.")
            elif del_btn.collidepoint(event.pos):
                db.delete_question(q_id)
                print(f"Deleted Question ID {q_id}")


def handle_select_question_type(event, buttons):
    global current_state, selected_question_type, question_data
    back_btn, multiple_choice_btn, fill_in_blank_btn, open_ended_btn = buttons
    if back_btn.collidepoint(event.pos):
        current_state = VIEW_GROUP
    elif multiple_choice_btn.collidepoint(event.pos):
        selected_question_type = "multiple_choice"
        question_data = {
            "question": "",
            "question_type": "multiple_choice",
            "options": [
                {"text": "", "is_correct": False},
                {"text": "", "is_correct": False},
            ],
            "points": 10,
            "category": "",
            "is_edit": False,
        }
        current_state = ADD_QUESTIONS
    elif fill_in_blank_btn.collidepoint(event.pos):
        selected_question_type = "fill_in_blank"
        question_data = {
            "question": "",
            "blank_text": "",
            "question_type": "fill_in_blank",
            "points": 10,
            "category": "",
            "is_edit": False,
        }
        current_state = ADD_QUESTIONS
    elif open_ended_btn.collidepoint(event.pos):
        selected_question_type = "open_ended"
        question_data = {
            "question": "",
            "question_type": "open_ended",
            "points": 10,
            "category": "",
            "is_edit": False,
        }
        current_state = ADD_QUESTIONS


def handle_add_questions_click(event, buttons):
    global current_state, question_data, focused_field
    back_btn, input_fields, add_choice_btn, save_btn = buttons

    if back_btn.collidepoint(event.pos):
        current_state = SELECT_QUESTION_TYPE
        return

    if add_choice_btn and add_choice_btn.collidepoint(event.pos):
        question_data["options"].append({"text": "", "is_correct": False})
        return

    if save_btn.collidepoint(event.pos):
        qtype = question_data.get("question_type")
        if qtype == "multiple_choice":
            opts = question_data.get("options", [])
            if not any(o["is_correct"] for o in opts):
                print("You must select a correct answer before saving!")
                return
        elif qtype == "fill_in_blank":
            blank_text = question_data.get("blank_text", "")
            main_question = question_data.get("question", "")
            if not blank_text:
                print("Fill in the blank text cannot be empty!")
                return
            pattern = r"\b" + re.escape(blank_text) + r"\b"
            if not re.search(pattern, main_question):
                print(
                    "Your fill-in text must appear as a *complete word* in the question!"
                )
                return

        if question_data.get("is_edit"):
            qid = question_data["question_id"]
            db.update_question(
                {
                    "question_id": qid,
                    "question_group_id": selected_question_group_id,
                    "question": question_data["question"],
                    "points": question_data["points"],
                    "category": question_data["category"],
                    "question_type": qtype,
                    "blank_text": question_data.get("blank_text", None),
                    "options": question_data.get("options", []),
                }
            )
        else:
            db.insert_question(
                {
                    "question_group_id": selected_question_group_id,
                    "question": question_data.get("question", ""),
                    "points": question_data.get("points", 10),
                    "category": question_data.get("category", ""),
                    "question_type": qtype,
                    "blank_text": question_data.get("blank_text", None),
                    "options": question_data.get("options", []),
                }
            )
        print(f"Saved/Updated Question: {question_data}")
        question_data.clear()
        current_state = VIEW_GROUP
        return

    for name, rect in input_fields:
        if rect.collidepoint(event.pos):
            focused_field = name
            return


def handle_add_questions_keydown(event):
    """
    Handle typing on the Add Questions screen.
    """
    global question_data, focused_field

    if not focused_field:
        return

    def handle_text_append(current_str, evt):
        if evt.key == pygame.K_BACKSPACE:
            return current_str[:-1]
        else:
            return current_str + evt.unicode

    if focused_field == "question":
        question_data["question"] = handle_text_append(question_data["question"], event)

    elif focused_field == "points":
        if event.key == pygame.K_BACKSPACE:
            question_data["points"] = str(question_data["points"])[:-1]
            if question_data["points"] == "":
                question_data["points"] = "0"
        else:
            if event.unicode.isdigit():
                question_data["points"] = str(question_data["points"]) + event.unicode

    elif focused_field == "category":
        if event.key == pygame.K_BACKSPACE:
            question_data["category"] = question_data["category"][:-1]
        else:
            question_data["category"] += event.unicode

    elif focused_field == "blank_text":
        question_data["blank_text"] = handle_text_append(
            question_data["blank_text"], event
        )

    elif focused_field.startswith("option_"):
        idx = int(focused_field.split("_")[1])
        if event.key == pygame.K_BACKSPACE:
            question_data["options"][idx]["text"] = question_data["options"][idx][
                "text"
            ][:-1]
        else:
            question_data["options"][idx]["text"] += event.unicode


def handle_add_questions_toggle_correct(field_name):
    """
    Mark one option as correct, the rest false.
    """
    global question_data
    idx = int(field_name.split("_")[2])
    for i, opt in enumerate(question_data["options"]):
        opt["is_correct"] = i == idx


def handle_session_setup(event, buttons):
    """Handle session setup events."""
    global current_state, session_setup_data, focused_field
    back_btn, group_buttons, time_box, create_session_btn = buttons

    if back_btn.collidepoint(event.pos):
        current_state = MAIN_MENU
        return

    for btn, gid in group_buttons:
        if btn.collidepoint(event.pos):
            # Store only the numeric ID
            session_setup_data["question_group_id"] = int(gid)
            print(f"[UI] Chose group {gid}")

    if time_box.collidepoint(event.pos):
        focused_field = "time_per_question"
        return

    if create_session_btn.collidepoint(event.pos):
        if not session_setup_data["question_group_id"]:
            print("[UI] No group selected!")
            return
        try:
            tpq = int(session_setup_data["time_per_question"])
        except ValueError:
            print("[UI] Invalid time-per-question input.")
            return
            
        # Create session using the game_logic instance which has a db instance
        sid = game_logic.create_new_session(tpq, int(session_setup_data["question_group_id"]))
        print(f"[UI] Created session {sid}")
        global team_list
        team_list = []
        current_state = TEAM_SETUP


def handle_session_setup_keydown(event):
    global session_setup_data, focused_field
    if focused_field != "time_per_question":
        return
    if event.key == pygame.K_BACKSPACE:
        session_setup_data["time_per_question"] = session_setup_data[
            "time_per_question"
        ][:-1]
    else:
        if event.unicode.isdigit():
            session_setup_data["time_per_question"] += event.unicode


def handle_team_setup(event, buttons):
    global current_state, team_input_text, team_list, focused_field, question_data
    back_btn, team_box, add_team_btn, done_btn = buttons

    if back_btn.collidepoint(event.pos):
        current_state = SESSION_SETUP
        return

    if team_box.collidepoint(event.pos):
        focused_field = "new_team_name"
        return

    if add_team_btn.collidepoint(event.pos):
        nm = team_input_text.strip()
        if nm:
            team_list.append(nm)
            print(f"[UI] Added team '{nm}'")
        team_input_text = ""
        return

    if done_btn.collidepoint(event.pos):
        if not team_list:
            print("[UI] Must add at least one team!")
            return
            
        # Set up teams
        game_logic.setup_teams(team_list)
        
        # Initialize question state
        question_data.clear()  # Clear any old state
        question_data["active_question"] = None
        
        print("[UI] Teams set up! Moving to gameplay.")
        current_state = GAMEPLAY


def handle_team_setup_keydown(event):
    global team_input_text, focused_field
    if focused_field != "new_team_name":
        return
    if event.key == pygame.K_BACKSPACE:
        team_input_text = team_input_text[:-1]
    else:
        team_input_text += event.unicode


def handle_gameplay(event, buttons):
    global current_state, question_data, focused_field
    end_btn, _, clickable_buttons, _ = buttons

    if end_btn and end_btn.collidepoint(event.pos):
        game_logic.end_session()
        question_data["active_question"] = None
        current_state = MAIN_MENU
        return

    if clickable_buttons:
        for btn_type, idx, rect in clickable_buttons:
            if rect.collidepoint(event.pos):
                if btn_type == "MC_OPTION":
                    handle_multiple_choice_click(idx)
                    return

                elif btn_type == "FILL_SUBMIT":
                    handle_fill_in_blank_submit()
                    return

                elif btn_type == "FILL_BOX":
                    focused_field = "user_answer"
                    return

                elif btn_type == "OPEN_CORRECT":
                    handle_open_ended_correct(True)
                    return

                elif btn_type == "OPEN_WRONG":
                    handle_open_ended_correct(False)
                    return


def handle_gameplay_keydown(event):
    global question_data, focused_field
    if focused_field == "user_answer":
        if event.key == pygame.K_BACKSPACE:
            question_data["user_answer"] = question_data["user_answer"][:-1]
        else:
            question_data["user_answer"] += event.unicode


def handle_multiple_choice_click(option_index):
    aq = question_data.get("active_question", None)
    if not aq:
        return

    options = aq.get("options", [])
    if option_index < 0 or option_index >= len(options):
        return

    chosen = options[option_index]
    was_correct = chosen["is_correct"]
    pts = aq.get("points", 0)
    print(f"[UI] User clicked option '{chosen['text']}', was_correct={was_correct}")

    game_logic.mark_answer(aq["id"], was_correct, pts)

    question_data["last_was_correct"] = was_correct
    if was_correct:
        question_data["last_points"] = pts
    else:
        question_data["last_points"] = 0

    question_data["active_question"] = None
    global current_state
    current_state = FEEDBACK


def handle_fill_in_blank_submit():
    aq = question_data.get("active_question", None)
    if not aq:
        return
    typed_ans = question_data.get("user_answer", "").strip()
    correct = aq.get("fill_in_blank_text", "")
    was_correct = typed_ans.lower() == correct.lower()
    pts = aq.get("points", 0)
    print(
        f"[UI] Fill in blank submitted='{typed_ans}', correct='{correct}', was_correct={was_correct}"
    )

    game_logic.mark_answer(aq["id"], was_correct, pts)

    question_data["active_question"] = None
    question_data["user_answer"] = ""
    question_data["last_was_correct"] = was_correct
    question_data["last_points"] = pts if was_correct else 0
    global current_state
    current_state = FEEDBACK


def handle_open_ended_correct(is_correct):
    aq = question_data.get("active_question", None)
    if not aq:
        return
    pts = aq.get("points", 0)
    was_correct = bool(is_correct)
    print(f"[UI] Open ended judged correct={was_correct}")

    game_logic.mark_answer(aq["id"], was_correct, pts)
    question_data["active_question"] = None
    question_data["user_answer"] = ""
    question_data["last_was_correct"] = was_correct
    question_data["last_points"] = pts if was_correct else 0
    global current_state
    current_state = FEEDBACK


def handle_feedback(event, buttons):
    global current_state, question_data
    next_btn, end_btn = buttons

    if next_btn.collidepoint(event.pos):
        question_data["active_question"] = None
        question_data.pop("last_was_correct", None)

        current_state = GAMEPLAY
        return

    if end_btn.collidepoint(event.pos):
        game_logic.end_session()
        question_data.clear()
        current_state = MAIN_MENU
        return


# ---------------------------
# Main Loop
# ---------------------------
def main():
    global current_state, input_text, focused_field
    clock = pygame.time.Clock()
    running = True
    buttons = None

    while running:
        # Draw
        if current_state == MAIN_MENU:
            buttons = draw_main_menu(display_manager)
        elif current_state == MANAGE_GROUPS:
            buttons = draw_manage_groups(display_manager)
        elif current_state == ADD_GROUP:
            buttons = draw_add_group(display_manager, input_text)
        elif current_state == SELECT_GROUP:
            buttons = draw_select_group(display_manager)
        elif current_state == VIEW_GROUP:
            buttons = draw_view_group(display_manager, selected_question_group_id)
        elif current_state == SELECT_QUESTION_TYPE:
            buttons = draw_select_question_type(display_manager)
        elif current_state == ADD_QUESTIONS:
            buttons = draw_add_questions(display_manager)
        elif current_state == SESSION_SETUP:
            buttons = draw_session_setup(display_manager)
        elif current_state == TEAM_SETUP:
            buttons = draw_team_setup(display_manager)
        elif current_state == GAMEPLAY:
            buttons = draw_gameplay(display_manager)
        elif current_state == FEEDBACK:
            buttons = draw_feedback(display_manager)
        for event in pygame.event.get():
            if event.type == pygame.VIDEORESIZE:
                display_manager.update_display_size(event.w, event.h)
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                design_x, design_y = display_manager.unscale_pos(*event.pos)
                if current_state == MAIN_MENU:
                    handle_main_menu(event, buttons)
                elif current_state == MANAGE_GROUPS:
                    handle_manage_groups(event, buttons)
                elif current_state == ADD_GROUP:
                    handle_add_group(event, buttons)
                elif current_state == SELECT_GROUP:
                    handle_select_group(event, buttons)
                elif current_state == VIEW_GROUP:
                    handle_view_group(event, buttons)
                elif current_state == SELECT_QUESTION_TYPE:
                    handle_select_question_type(event, buttons)
                elif current_state == ADD_QUESTIONS:
                    handle_add_questions_click(event, buttons)
                    _, input_fields, _, _ = buttons
                    for field_name, rect in input_fields:
                        if rect.collidepoint(event.pos) and field_name.startswith(
                            "toggle_correct_"
                        ):
                            handle_add_questions_toggle_correct(field_name)
                            break
                elif current_state == SESSION_SETUP:
                    handle_session_setup(event, buttons)
                elif current_state == TEAM_SETUP:
                    handle_team_setup(event, buttons)
                elif current_state == GAMEPLAY:
                    handle_gameplay(event, buttons)
                elif current_state == FEEDBACK:
                    handle_feedback(event, buttons)
            if event.type == pygame.KEYDOWN:
                if current_state == ADD_GROUP:
                    if event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        input_text += event.unicode
                elif current_state == ADD_QUESTIONS:
                    handle_add_questions_keydown(event)
                elif current_state == SESSION_SETUP:
                    handle_session_setup_keydown(event)
                elif current_state == TEAM_SETUP:
                    handle_team_setup_keydown(event)
                elif current_state == GAMEPLAY:
                    handle_gameplay_keydown(event)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()
