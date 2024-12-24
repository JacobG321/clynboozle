import pygame
from db_manager import DBManager

# Initialize PyGame
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

# Fonts
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 28)

# Game States
MAIN_MENU = "MAIN_MENU"
MANAGE_GROUPS = "MANAGE_GROUPS"
ADD_GROUP = "ADD_GROUP"
SELECT_GROUP = "SELECT_GROUP"
VIEW_GROUP = "VIEW_GROUP"
SELECT_QUESTION_TYPE = "SELECT_QUESTION_TYPE"
ADD_QUESTIONS = "ADD_QUESTIONS"
current_state = MAIN_MENU

# Database Manager
db = DBManager()

# Focused Field
focused_field = None
selected_group_id = None
selected_question_type = None
question_data = {}

# Helper Functions
def create_button(x, y, width, height, color, text, text_color=WHITE):
    button_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, color, button_rect)
    button_text = font.render(text, True, text_color)
    screen.blit(button_text, (x + (width - button_text.get_width()) // 2, y + (height - button_text.get_height()) // 2))
    return button_rect

def draw_back_button():
    return create_button(50, 500, 100, 50, BLUE, "Back")

# Functions to Draw Each Screen
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
    groups = db.create_connection().cursor().execute("SELECT id, group_name FROM groups").fetchall()
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
    questions = db.create_connection().cursor().execute("SELECT id, question FROM questions WHERE group_id = ?", (group_id,)).fetchall()
    for question in questions:
        question_btn = create_button(50, y_offset, 600, 50, GRAY, f"{question[1]}")
        delete_btn = create_button(675, y_offset, 100, 50, RED, "Delete")
        question_buttons.append((question_btn, delete_btn, question[0]))
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
    y_offset = 150
    input_fields = []

    for key, value in question_data.items():
        label = font.render(f"{key.capitalize()}: ", True, BLACK)
        screen.blit(label, (50, y_offset))
        input_box = pygame.Rect(300, y_offset - 10, 400, 40)
        pygame.draw.rect(screen, GRAY, input_box)
        input_text_render = font.render(value, True, BLACK)
        screen.blit(input_text_render, (input_box.x + 5, input_box.y + 5))
        input_fields.append((key, input_box))
        y_offset += 60

    save_btn = create_button(300, y_offset, 200, 50, BLUE, "Save")
    return back_btn, input_fields, save_btn

# Event Handlers
def handle_main_menu(event, buttons):
    global current_state
    start_game_btn, manage_groups_btn, quit_btn = buttons
    if start_game_btn.collidepoint(event.pos):
        current_state = "GAMEPLAY"  # Placeholder for gameplay state
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
    global current_state, selected_group_id
    back_btn, group_buttons = buttons
    if back_btn.collidepoint(event.pos):
        current_state = MANAGE_GROUPS
    for group_btn, group_id in group_buttons:
        if group_btn.collidepoint(event.pos):
            selected_group_id = group_id
            current_state = VIEW_GROUP

def handle_view_group(event, buttons):
    global current_state
    back_btn, add_question_btn, delete_group_btn, question_buttons = buttons
    if back_btn.collidepoint(event.pos):
        current_state = SELECT_GROUP
    elif add_question_btn.collidepoint(event.pos):
        current_state = SELECT_QUESTION_TYPE
    elif delete_group_btn.collidepoint(event.pos):
        print("Delete Group - Placeholder")  # Placeholder for delete logic
    for question_btn, delete_btn, question_id in question_buttons:
        if question_btn.collidepoint(event.pos):
            print(f"Edit Question ID {question_id}")  # Placeholder for edit logic
        elif delete_btn.collidepoint(event.pos):
            print(f"Delete Question ID {question_id}")  # Placeholder for delete logic

def handle_select_question_type(event, buttons):
    global current_state, selected_question_type, question_data
    back_btn, multiple_choice_btn, fill_in_blank_btn, open_ended_btn = buttons
    if back_btn.collidepoint(event.pos):
        current_state = VIEW_GROUP
    elif multiple_choice_btn.collidepoint(event.pos):
        selected_question_type = "multiple_choice"
        question_data = {
            "question": "",
            "option1": "",
            "option2": "",
            "option3": "",
            "option4": "",
            "correct_option": ""
        }
        current_state = ADD_QUESTIONS
    elif fill_in_blank_btn.collidepoint(event.pos):
        selected_question_type = "fill_in_blank"
        question_data = {
            "question": "",
            "correct_answer": ""
        }
        current_state = ADD_QUESTIONS
    elif open_ended_btn.collidepoint(event.pos):
        selected_question_type = "open_ended"
        question_data = {
            "question": "",
            "model_answer": ""
        }
        current_state = ADD_QUESTIONS

def handle_add_questions(event, buttons):
    global current_state, question_data, focused_field
    back_btn, input_fields, save_btn = buttons
    if back_btn.collidepoint(event.pos):
        current_state = SELECT_QUESTION_TYPE
    elif save_btn.collidepoint(event.pos):
        db.insert_question({**question_data, "group_id": selected_group_id, "type": selected_question_type})
        print(f"Saved Question: {question_data}")  # Confirmation placeholder
        question_data = {}
        current_state = VIEW_GROUP
    for key, input_box in input_fields:
        if input_box.collidepoint(event.pos):
            focused_field = key

# Main Loop
running = True
input_text = ""
buttons = None
while running:
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

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

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
                handle_add_questions(event, buttons)

        if event.type == pygame.KEYDOWN and current_state in [ADD_GROUP, ADD_QUESTIONS]:
            if event.key == pygame.K_BACKSPACE and focused_field in question_data:
                question_data[focused_field] = question_data[focused_field][:-1]
            elif focused_field in question_data:
                question_data[focused_field] += event.unicode

    pygame.display.flip()
