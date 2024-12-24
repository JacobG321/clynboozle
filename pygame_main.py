import pygame
import re
from db_manager import DBManager
from game_logic import GameLogic  # <--- Our new game logic module

# ---------------------------
# PyGame Initialization
# ---------------------------
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Clynboozle GUI")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GRAY = (200, 200, 200)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
DARK_RED = (200, 0, 0)
DARK_GREEN = (0, 200, 0)

# Fonts
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 28)

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

# NEW STATES for the game flow
SESSION_SETUP = "SESSION_SETUP"
TEAM_SETUP = "TEAM_SETUP"
GAMEPLAY = "GAMEPLAY"

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
selected_group_id = None
selected_question_type = None
question_data = {}   # Holds question info (including editing vs. new)
input_text = ""      # Temporary input text for add_group screen

# For the game flow
session_setup_data = {
    "group_id": None,
    "time_per_question": "30",
}
team_list = []       # list of team names user adds
team_input_text = "" # used to type new team name

# ---------------------------
# Helper Functions
# ---------------------------
def create_button(x, y, width, height, color, text, text_color=WHITE):
    button_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, color, button_rect)
    button_text = font.render(text, True, text_color)
    screen.blit(
        button_text,
        (
            x + (width - button_text.get_width()) // 2,
            y + (height - button_text.get_height()) // 2
        )
    )
    return button_rect

def draw_back_button():
    return create_button(50, 500, 100, 50, BLUE, "Back")

# ---------------------------
# Draw Screens
# ---------------------------
def draw_main_menu():
    screen.fill(WHITE)
    title = font.render("Clynboozle", True, BLACK)
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

    start_game_btn = create_button(300, 200, 225, 50, BLUE, "Start Game")
    manage_groups_btn = create_button(300, 300, 225, 50, BLUE, "Manage Groups")
    quit_btn = create_button(300, 400, 225, 50, BLUE, "Quit")

    return start_game_btn, manage_groups_btn, quit_btn

def draw_manage_groups():
    screen.fill(WHITE)
    title = font.render("Manage Groups", True, BLACK)
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

    back_btn = draw_back_button()
    add_group_btn = create_button(300, 200, 200, 50, BLUE, "Add Group")
    select_group_btn = create_button(300, 300, 200, 50, BLUE, "View Groups")

    return back_btn, add_group_btn, select_group_btn

def draw_add_group(input_text):
    screen.fill(WHITE)
    title = font.render("Add New Group", True, BLACK)
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

    back_btn = draw_back_button()
    input_box = pygame.Rect(200, 250, 400, 50)
    pygame.draw.rect(screen, GRAY, input_box)
    input_text_render = font.render(input_text, True, BLACK)
    screen.blit(input_text_render, (input_box.x + 10, input_box.y + 10))

    save_btn = create_button(300, 350, 200, 50, BLUE, "Save")

    return back_btn, input_box, save_btn

def draw_select_group():
    screen.fill(WHITE)
    title = font.render("Select a Group", True, BLACK)
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

    back_btn = draw_back_button()

    group_buttons = []
    y_offset = 150

    conn = db.create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, group_name FROM groups")
    groups = cursor.fetchall()
    conn.close()

    for group in groups:
        group_btn = create_button(50, y_offset, 700, 50, BLUE, f"{group[0]}: {group[1]}")
        group_buttons.append((group_btn, group[0]))
        y_offset += 60

    return back_btn, group_buttons

def draw_view_group(group_id):
    screen.fill(WHITE)
    title = font.render(f"Group {group_id} Questions", True, BLACK)
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

    back_btn = draw_back_button()
    add_question_btn = create_button(300, 500, 200, 50, BLUE, "Add Question")
    delete_group_btn = create_button(600, 500, 200, 50, RED, "Delete Group")

    question_buttons = []
    y_offset = 150

    questions = db.get_questions_for_group(group_id)
    for q in questions:
        q_btn = create_button(50, y_offset, 600, 50, GRAY, f"{q['question']}")
        del_btn = create_button(675, y_offset, 100, 50, RED, "Delete")
        question_buttons.append((q_btn, del_btn, q['id']))
        y_offset += 60

    return back_btn, add_question_btn, delete_group_btn, question_buttons

def draw_select_question_type():
    screen.fill(WHITE)
    title = font.render("Select Question Type", True, BLACK)
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

    back_btn = draw_back_button()
    multiple_choice_btn = create_button(300, 200, 300, 50, BLUE, "Multiple Choice")
    fill_in_blank_btn = create_button(300, 300, 300, 50, BLUE, "Fill in the Blank")
    open_ended_btn = create_button(300, 400, 300, 50, BLUE, "Open Ended")

    return back_btn, multiple_choice_btn, fill_in_blank_btn, open_ended_btn

def draw_add_questions():
    screen.fill(WHITE)
    title = font.render("Add Question Details", True, BLACK)
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

    back_btn = draw_back_button()
    y_offset = 120
    input_fields = []

    # Question text
    label_q = small_font.render("Question:", True, BLACK)
    screen.blit(label_q, (50, y_offset))
    question_box = pygame.Rect(200, y_offset - 5, 500, 36)
    pygame.draw.rect(screen, GRAY, question_box)
    text_render = small_font.render(question_data.get("question", ""), True, BLACK)
    screen.blit(text_render, (question_box.x + 5, question_box.y + 5))
    input_fields.append(("question", question_box))
    y_offset += 50

    add_choice_btn = None

    # If multiple choice
    if question_data.get("question_type") == "multiple_choice":
        options = question_data.get("options", [])
        for i, opt in enumerate(options):
            label_opt = small_font.render(f"Option {i+1}:", True, BLACK)
            screen.blit(label_opt, (50, y_offset))

            box_color = GREEN if opt.get("is_correct") else GRAY
            option_box = pygame.Rect(200, y_offset - 5, 400, 36)
            pygame.draw.rect(screen, box_color, option_box)
            option_text_render = small_font.render(opt["text"], True, BLACK)
            screen.blit(option_text_render, (option_box.x + 5, option_box.y + 5))
            input_fields.append((f"option_{i}", option_box))

            toggle_correct_btn = pygame.Rect(610, y_offset - 5, 30, 36)
            toggle_color = DARK_GREEN if opt.get("is_correct") else DARK_RED
            pygame.draw.rect(screen, toggle_color, toggle_correct_btn)
            input_fields.append((f"toggle_correct_{i}", toggle_correct_btn))

            y_offset += 50

        add_choice_btn = create_button(50, y_offset, 150, 40, BLUE, "Add Choice")
        y_offset += 60

    # If fill in blank
    elif question_data.get("question_type") == "fill_in_blank":
        label_blank = small_font.render("Fill-in text:", True, BLACK)
        screen.blit(label_blank, (50, y_offset))
        blank_box = pygame.Rect(200, y_offset - 5, 300, 36)
        pygame.draw.rect(screen, GRAY, blank_box)
        blank_text_render = small_font.render(
            str(question_data.get("blank_text", "")), True, BLACK
        )
        screen.blit(blank_text_render, (blank_box.x + 5, blank_box.y + 5))
        input_fields.append(("blank_text", blank_box))
        y_offset += 50

    # Points
    label_points = small_font.render("Points:", True, BLACK)
    screen.blit(label_points, (50, y_offset))
    points_box = pygame.Rect(200, y_offset - 5, 100, 36)
    pygame.draw.rect(screen, GRAY, points_box)
    points_text_render = small_font.render(str(question_data.get("points", "10")), True, BLACK)
    screen.blit(points_text_render, (points_box.x + 5, points_box.y + 5))
    input_fields.append(("points", points_box))
    y_offset += 50

    # Category
    label_cat = small_font.render("Category:", True, BLACK)
    screen.blit(label_cat, (50, y_offset))
    cat_box = pygame.Rect(200, y_offset - 5, 300, 36)
    pygame.draw.rect(screen, GRAY, cat_box)
    cat_text_render = small_font.render(str(question_data.get("category", "")), True, BLACK)
    screen.blit(cat_text_render, (cat_box.x + 5, cat_box.y + 5))
    input_fields.append(("category", cat_box))
    y_offset += 50

    # Save/Update
    save_btn = create_button(
        300, y_offset, 200, 50, BLUE,
        "Update" if question_data.get("is_edit") else "Save"
    )

    return back_btn, input_fields, add_choice_btn, save_btn

# ---------------------------
# NEW SCREENS FOR GAME LOGIC
# ---------------------------
def draw_session_setup():
    screen.fill(WHITE)
    title = font.render("Session Setup", True, BLACK)
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

    # Show groups to pick from
    y_offset = 120
    group_label = small_font.render("Select Group ID:", True, BLACK)
    screen.blit(group_label, (50, y_offset))

    conn = db.create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, group_name FROM groups ORDER BY id ASC;")
    rows = cursor.fetchall()
    conn.close()

    group_buttons = []
    gx = 250
    for (gid, gname) in rows:
        txt = f"{gid}: {gname}"
        btn = create_button(gx, y_offset, 250, 40, (0, 200, 200), txt, BLACK)
        group_buttons.append((btn, gid))
        gx += 260
        if gx + 250 > SCREEN_WIDTH:
            gx = 250
            y_offset += 60

    y_offset += 80
    time_label = small_font.render("Time per Question (sec):", True, BLACK)
    screen.blit(time_label, (50, y_offset))
    time_box = pygame.Rect(300, y_offset - 5, 100, 36)
    pygame.draw.rect(screen, GRAY, time_box)
    t_render = small_font.render(session_setup_data["time_per_question"], True, BLACK)
    screen.blit(t_render, (time_box.x + 5, time_box.y + 5))

    y_offset += 70
    create_session_btn = create_button(300, y_offset, 200, 50, BLUE, "Create Session")
    back_btn = draw_back_button()

    return back_btn, group_buttons, time_box, create_session_btn

def draw_team_setup():
    screen.fill(WHITE)
    title = font.render("Team Setup", True, BLACK)
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

    y_offset = 120
    t_label = small_font.render("Current Teams:", True, BLACK)
    screen.blit(t_label, (50, y_offset))
    y_offset += 40
    for nm in team_list:
        txt = small_font.render(f"- {nm}", True, BLACK)
        screen.blit(txt, (70, y_offset))
        y_offset += 30

    # Input for new team
    y_offset += 20
    new_team_label = small_font.render("Add Team Name:", True, BLACK)
    screen.blit(new_team_label, (50, y_offset))
    team_box = pygame.Rect(250, y_offset - 5, 300, 36)
    pygame.draw.rect(screen, GRAY, team_box)
    team_text_render = small_font.render(team_input_text, True, BLACK)
    screen.blit(team_text_render, (team_box.x + 5, team_box.y + 5))

    y_offset += 60
    add_team_btn = create_button(50, y_offset, 150, 40, BLUE, "Add Team")
    done_btn = create_button(250, y_offset, 150, 40, GREEN, "Done")

    back_btn = draw_back_button()

    return back_btn, team_box, add_team_btn, done_btn

def draw_gameplay():
    screen.fill(WHITE)
    # If no session or session is inactive, show a message
    if not game_logic.current_session_id:
        msg = font.render("No Active Session!", True, RED)
        screen.blit(msg, (50, 50))
        end_btn = create_button(300, 500, 200, 50, RED, "Back to Menu")
        return end_btn, None, None

    s_data = db.get_session(game_logic.current_session_id)
    if not s_data or not s_data["is_active"]:
        msg = font.render("Session is not active!", True, RED)
        screen.blit(msg, (50, 50))
        end_btn = create_button(300, 500, 200, 50, RED, "Back to Menu")
        return end_btn, None, None

    # Check if we have an active question
    if "active_question" not in question_data:
        # Attempt to fetch a new question
        q = game_logic.begin_game_loop()
        if q is None:
            question_data["active_question"] = None
        else:
            question_data["active_question"] = q
            question_data["user_answer"] = ""

    aq = question_data["active_question"]
    y_offset = 50
    if aq is None:
        msg = font.render("No more questions or session done!", True, RED)
        screen.blit(msg, (50, y_offset))
        y_offset += 60
        end_btn = create_button(300, 500, 200, 50, RED, "End Session")
        return end_btn, None, None

    # Display question text
    qtype = aq["question_type"]
    q_text = aq["question"]

    # If fill_in_blank, mask the blank text
    if qtype == "fill_in_blank" and aq.get("fill_in_blank_text"):
        pat = re.escape(aq["fill_in_blank_text"])
        q_text = re.sub(pat, "_____", q_text, flags=re.IGNORECASE)

    quest_surf = small_font.render(q_text, True, BLACK)
    screen.blit(quest_surf, (50, y_offset))
    y_offset += 40

    # user_answer box
    ans_label = small_font.render("Your answer:", True, BLACK)
    screen.blit(ans_label, (50, y_offset))
    ans_box = pygame.Rect(200, y_offset - 5, 300, 36)
    pygame.draw.rect(screen, GRAY, ans_box)
    ans_text = question_data.get("user_answer", "")
    ans_surf = small_font.render(ans_text, True, BLACK)
    screen.blit(ans_surf, (ans_box.x+5, ans_box.y+5))

    submit_btn = create_button(520, y_offset - 5, 100, 40, GREEN, "Submit")

    y_offset += 70
    # Show scores
    scores_label = small_font.render("Scores:", True, BLACK)
    screen.blit(scores_label, (50, y_offset))
    y_offset += 30

    st = game_logic.get_scores()
    for tid, sc in st.items():
        team_surf = small_font.render(f"Team {tid}: {sc}", True, BLACK)
        screen.blit(team_surf, (70, y_offset))
        y_offset += 30

    end_btn = create_button(50, 500, 200, 50, RED, "End Session")
    return end_btn, ans_box, submit_btn

# ---------------------------
# Event Handlers
# ---------------------------
def handle_main_menu(event, buttons):
    global current_state
    start_game_btn, manage_groups_btn, quit_btn = buttons
    if start_game_btn.collidepoint(event.pos):
        current_state = SESSION_SETUP  # Jump to session setup
    elif manage_groups_btn.collidepoint(event.pos):
        current_state = MANAGE_GROUPS
    elif quit_btn.collidepoint(event.pos):
        pygame.quit()
        exit()

# Existing "manage groups" event handlers remain as is...
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
    global current_state, selected_group_id
    back_btn, group_buttons = buttons
    if back_btn.collidepoint(event.pos):
        current_state = MANAGE_GROUPS
    else:
        for group_btn, g_id in group_buttons:
            if group_btn.collidepoint(event.pos):
                selected_group_id = g_id
                current_state = VIEW_GROUP

def handle_view_group(event, buttons):
    global current_state, question_data
    back_btn, add_question_btn, delete_group_btn, question_buttons = buttons
    if back_btn.collidepoint(event.pos):
        current_state = SELECT_GROUP
    elif add_question_btn.collidepoint(event.pos):
        current_state = SELECT_QUESTION_TYPE
    elif delete_group_btn.collidepoint(event.pos):
        db.delete_group(selected_group_id)
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
                        question_data["blank_text"] = existing_q.get("fill_in_blank_text", "")
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
                {"text": "", "is_correct": False}
            ],
            "points": 10,
            "category": "",
            "is_edit": False
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
            "is_edit": False
        }
        current_state = ADD_QUESTIONS
    elif open_ended_btn.collidepoint(event.pos):
        selected_question_type = "open_ended"
        question_data = {
            "question": "",
            "question_type": "open_ended",
            "points": 10,
            "category": "",
            "is_edit": False
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
                print("Your fill-in text must appear as a *complete word* in the question!")
                return

        if question_data.get("is_edit"):
            qid = question_data["question_id"]
            db.update_question({
                "question_id": qid,
                "group_id": selected_group_id,
                "question": question_data["question"],
                "points": question_data["points"],
                "category": question_data["category"],
                "question_type": qtype,
                "blank_text": question_data.get("blank_text", None),
                "options": question_data.get("options", [])
            })
        else:
            db.insert_question({
                "group_id": selected_group_id,
                "question": question_data.get("question", ""),
                "points": question_data.get("points", 10),
                "category": question_data.get("category", ""),
                "question_type": qtype,
                "blank_text": question_data.get("blank_text", None),
                "options": question_data.get("options", [])
            })
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
        # Only allow digits, or backspace
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
        question_data["blank_text"] = handle_text_append(question_data["blank_text"], event)

    elif focused_field.startswith("option_"):
        idx = int(focused_field.split("_")[1])
        if event.key == pygame.K_BACKSPACE:
            question_data["options"][idx]["text"] = question_data["options"][idx]["text"][:-1]
        else:
            question_data["options"][idx]["text"] += event.unicode

def handle_add_questions_toggle_correct(field_name):
    """
    Mark one option as correct, the rest false.
    """
    global question_data
    idx = int(field_name.split("_")[2])  # e.g. "toggle_correct_0" -> idx=0
    for i, opt in enumerate(question_data["options"]):
        opt["is_correct"] = (i == idx)

# ---------------------------
# NEW EVENT HANDLERS
# ---------------------------
def handle_session_setup(event, buttons):
    global current_state, session_setup_data, focused_field
    back_btn, group_buttons, time_box, create_session_btn = buttons

    if back_btn.collidepoint(event.pos):
        current_state = MAIN_MENU
        return

    for (btn, gid) in group_buttons:
        if btn.collidepoint(event.pos):
            session_setup_data["group_id"] = gid
            print(f"[UI] Chose group {gid}")

    if time_box.collidepoint(event.pos):
        focused_field = "time_per_question"
        return

    if create_session_btn.collidepoint(event.pos):
        if not session_setup_data["group_id"]:
            print("[UI] No group selected!")
            return
        try:
            tpq = int(session_setup_data["time_per_question"])
        except ValueError:
            print("[UI] Invalid time-per-question input.")
            return
        sid = game_logic.create_new_session(session_setup_data["group_id"], tpq)
        print(f"[UI] Created session {sid}")
        # Clear team list
        global team_list
        team_list = []
        current_state = TEAM_SETUP

def handle_session_setup_keydown(event):
    global session_setup_data, focused_field
    if focused_field != "time_per_question":
        return
    if event.key == pygame.K_BACKSPACE:
        session_setup_data["time_per_question"] = session_setup_data["time_per_question"][:-1]
    else:
        if event.unicode.isdigit():
            session_setup_data["time_per_question"] += event.unicode

def handle_team_setup(event, buttons):
    global current_state, team_input_text, team_list, focused_field
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
        game_logic.setup_teams(team_list)
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
    end_btn, ans_box, submit_btn = buttons

    if end_btn and end_btn.collidepoint(event.pos):
        game_logic.end_session()
        question_data["active_question"] = None
        current_state = MAIN_MENU
        return

    if ans_box and ans_box.collidepoint(event.pos):
        focused_field = "user_answer"
        return

    if submit_btn and submit_btn.collidepoint(event.pos):
        aq = question_data.get("active_question", None)
        if not aq:
            return
        user_ans = question_data.get("user_answer", "").strip()
        qtype = aq["question_type"]
        was_correct = False
        pts = aq.get("points", 0)

        if qtype == "fill_in_blank":
            correct = aq.get("fill_in_blank_text", "")
            was_correct = (user_ans.lower() == correct.lower())
        elif qtype == "multiple_choice":
            # simplified approach:
            correct_opts = [o["text"] for o in aq.get("options", []) if o["is_correct"]]
            was_correct = any(user_ans.lower() == c.lower() for c in correct_opts)
        elif qtype == "open_ended":
            # If user types 'yes', we consider correct
            was_correct = (user_ans.lower() == "yes")

        print(f"[UI] Submitted answer='{user_ans}', was_correct={was_correct}")
        game_logic.mark_answer(aq["id"], was_correct, pts)
        # Force next question load
        question_data["active_question"] = None
        question_data["user_answer"] = ""

def handle_gameplay_keydown(event):
    global question_data, focused_field
    if focused_field != "user_answer":
        return
    if event.key == pygame.K_BACKSPACE:
        question_data["user_answer"] = question_data["user_answer"][:-1]
    else:
        question_data["user_answer"] += event.unicode

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
            buttons = draw_main_menu()
        elif current_state == MANAGE_GROUPS:
            buttons = draw_manage_groups()
        elif current_state == ADD_GROUP:
            buttons = draw_add_group(input_text)
        elif current_state == SELECT_GROUP:
            buttons = draw_select_group()
        elif current_state == VIEW_GROUP:
            buttons = draw_view_group(selected_group_id)
        elif current_state == SELECT_QUESTION_TYPE:
            buttons = draw_select_question_type()
        elif current_state == ADD_QUESTIONS:
            buttons = draw_add_questions()

        # New screens
        elif current_state == SESSION_SETUP:
            buttons = draw_session_setup()
        elif current_state == TEAM_SETUP:
            buttons = draw_team_setup()
        elif current_state == GAMEPLAY:
            buttons = draw_gameplay()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
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
                    # Then check toggles
                    _, input_fields, _, _ = buttons
                    for field_name, rect in input_fields:
                        if rect.collidepoint(event.pos) and field_name.startswith("toggle_correct_"):
                            handle_add_questions_toggle_correct(field_name)
                            break

                elif current_state == SESSION_SETUP:
                    handle_session_setup(event, buttons)
                elif current_state == TEAM_SETUP:
                    handle_team_setup(event, buttons)
                elif current_state == GAMEPLAY:
                    handle_gameplay(event, buttons)

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
