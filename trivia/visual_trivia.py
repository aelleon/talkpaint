import time
import ollama
import subprocess
import json
import threading
import cv2
from arduino_setup import win

MODEL_TO_USE = "gemma3:latest"
DEFAULT_RATE = 180  # Default speech rate for TTS
TOTAL_QUESTIONS = 5
WIN_TOTAL = 4  # Minimum score to win the game
BOX_LOCATIONS = [(650, 300), (650, 1300), (350, 800), (1000, 800)]
TEXT_MAIN_COLOR = (0, 0, 0)
TEXT_SELECTION_COLOR = (255, 0, 0)  # Color for selected text

END_GAME = {
    "game_over": False,
}
image = None  # Placeholder for the image to be displayed during the game


def say(text, background=False, rate=DEFAULT_RATE):
    if background:
        subprocess.Popen(["say", f"-r {rate}", text])
    else:
        subprocess.call(["say", f"-r {rate}", text])


def get_trivia_questions(subject, retry_count=3, number_of_questions=10):
    if retry_count <= 0:
        print("Failed to get trivia questions after multiple attempts.")
        return []

    first_sentence = (
        f"Generate {number_of_questions} new unique multiple-choice questions about '{subject}' that gradually get harder."
        if number_of_questions > 1
        else f"Generate a new unique multiple-choice question about '{subject}'."
    )
    initial_prompt = (
        f"{first_sentence}."
        "Do not repeat questions or answers from previous requests. "
        "Make answers choices as only one word or short phrases."
        "Make questions concise and clear. "
        "Do not include anything inappropriate or offensive. "
        "Return them as a JSON array, each item formatted as: "
        "{ question: string, answerChoices: string[], answer: string }."
        "question is the question text, answerChoices is an array of possible answers, answer is the full text of the correct answer."
    )

    start = time.time()
    response = ollama.chat(
        model=MODEL_TO_USE, messages=[{"role": "user", "content": initial_prompt}]
    )
    end = time.time()
    print(f"Response time: {end - start:.2f} seconds")

    response_text = response["message"]["content"]
    print(f"AI: {response_text}")

    try:
        clean_json = (
            response_text.strip("`")
            .split("\n", 1)[1]
            .rsplit("\n", 1)[0]
            .replace("‘", "'")
        )
        questions = json.loads(clean_json)
        return questions
    except json.JSONDecodeError:
        print("Error decoding JSON response from AI")
        if retry_count > 0:
            print(f"{retry_count} retries left")
            print("Retrying to get trivia questions...")
            return get_trivia_questions(subject, retry_count - 1)


def wrap_text(text, font_face, font_scale, thickness, max_width):
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        current_line.append(word)
        # Check the width of the current line
        (width, height), baseline = cv2.getTextSize(
            " ".join(current_line), font_face, font_scale, thickness
        )

        if width > max_width and len(current_line) > 1:
            # Remove the last word and add the current line to lines
            current_line.pop()
            lines.append(" ".join(current_line))
            # Start new line with the word that didn't fit
            current_line = [word]

    # Add the last line
    if current_line:
        lines.append(" ".join(current_line))

    return lines


def ask_question(question, answer_choices, answer, question_number, score):
    global image
    # Create a clean copy of the background image for this question
    image = cv2.imread("background.png")
    if image is None:
        print("Error: Could not load background.png")
        return

    question_number = question_number + 1
    question_str = f"\nQuestion {question_number}: {question}"

    # Wrap and draw the question at the top of the image
    max_width = image.shape[1] - 40  # Leave 20px margin on each side
    question_lines = wrap_text(question, cv2.FONT_HERSHEY_SIMPLEX, 1, 2, max_width)

    # Draw each line of the question
    y_offset = 30
    for line in question_lines:
        cv2.putText(
            image, line, (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 1, TEXT_MAIN_COLOR, 2
        )
        y_offset += 40  # Space between lines

    cv2.imshow("Trivia Game", image)
    cv2.waitKey(1)  # Allow the image to be displayed

    say(question_str)

    for j, choice in enumerate(answer_choices):
        # Calculate the size of the text and wrap if necessary
        max_choice_width = 400  # Maximum width for answer choices
        choice_lines = wrap_text(
            choice, cv2.FONT_HERSHEY_SIMPLEX, 2, 5, max_choice_width
        )

        # Get the center point from BOX_LOCATIONS
        center_x, center_y = BOX_LOCATIONS[j]

        # Calculate total height of wrapped text
        total_height = len(choice_lines) * 60  # 60 pixels between lines

        # Draw each line of the answer, centered
        for i, line in enumerate(choice_lines):
            (text_width, text_height), baseline = cv2.getTextSize(
                line, cv2.FONT_HERSHEY_SIMPLEX, 2, 5
            )
            # Adjust y position for multiple lines
            y_pos = center_y - (total_height // 2) + (i * 60)
            # Center the text horizontally
            x_pos = center_x - (text_width // 2)

            cv2.putText(
                image,
                line,
                (x_pos, y_pos),
                cv2.FONT_HERSHEY_SIMPLEX,
                2,
                TEXT_MAIN_COLOR,
                5,
            )

        cv2.imshow("Trivia Game", image)
        cv2.waitKey(1)  # Allow the image to be displayed
        say(f"{chr(65 + j)}.")
        say(choice, rate=DEFAULT_RATE + 20)

    user_answer = None
    selected_index = -1  # Keep track of which answer is currently selected
    startTime = time.time()
    currentTime = startTime
    timeout = 4  # 4 seconds timer
    bar_width = image.shape[1] - 40  # Full width of the timer bar
    bar_height = 20  # Height of the timer bar
    bar_y = image.shape[0] - 50  # Position the bar near the bottom

    while (currentTime - startTime) < timeout:
        # Create a copy of the current image to draw the timer bar and selections
        display_image = image.copy()

        # Redraw all choices, highlighting the selected one
        for j, choice in enumerate(answer_choices):
            color = TEXT_SELECTION_COLOR if j == selected_index else TEXT_MAIN_COLOR

            # Wrap and redraw the choice with new color
            choice_lines = wrap_text(
                choice, cv2.FONT_HERSHEY_SIMPLEX, 2, 5, max_choice_width
            )
            center_x, center_y = BOX_LOCATIONS[j]
            total_height = len(choice_lines) * 60

            for i, line in enumerate(choice_lines):
                (text_width, text_height), baseline = cv2.getTextSize(
                    line, cv2.FONT_HERSHEY_SIMPLEX, 2, 5
                )
                y_pos = center_y - (total_height // 2) + (i * 60)
                x_pos = center_x - (text_width // 2)

                cv2.putText(
                    display_image,
                    line,
                    (x_pos, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    2,
                    color,
                    5,
                )

        # Calculate remaining time and bar width
        elapsed = currentTime - startTime
        remaining_ratio = 1 - (elapsed / timeout)
        current_bar_width = int(bar_width * remaining_ratio)

        # Draw the timer bar
        cv2.rectangle(
            display_image,
            (20, bar_y),
            (20 + bar_width, bar_y + bar_height),
            (100, 100, 100),
            -1,
        )  # Background bar
        cv2.rectangle(
            display_image,
            (20, bar_y),
            (20 + current_bar_width, bar_y + bar_height),
            TEXT_SELECTION_COLOR,
            -1,
        )  # Time remaining

        # Show the image with the timer bar and selections
        cv2.imshow("Trivia Game", display_image)
        key = cv2.waitKey(10)
        if key >= 0 and key <= 3:
            selected_index = key
            user_answer = answer_choices[key]

        currentTime = time.time()

    # Show the final state of the timer
    if user_answer == None:
        say(f"Time's up! The correct answer was: {answer}")
    elif user_answer == answer:
        say("Correct!")
        score += 1
    else:
        say(f"Wrong! The correct answer was: {answer}")

    # Display the final state for a moment
    cv2.waitKey(500)
    return score


def run_trivia_game():
    global image  # Declare image as global
    topic_question = "Give me a topic to ask questions about"
    say(topic_question, background=True)
    subject = input(topic_question + ": ")

    # Load the image and check if it was loaded successfully
    image = cv2.imread("background.png")
    if image is None:
        print("Error: Could not load background.png")
        return

    cv2.imshow("Trivia Game", image)
    cv2.waitKey(1)  # Allow the image to be displayed
    say(
        f"Let me think of some questions about {subject}.",
        rate=DEFAULT_RATE + 20,
        background=True,
    )
    ai_response = get_trivia_questions(subject, number_of_questions=1)
    print("=================== Game Start ===================")

    if not ai_response:
        print("No questions available for the given topic.")
        return

    questions = [response["question"] for response in ai_response]
    answer_choices = [response["answerChoices"] for response in ai_response]
    answers = [response["answer"] for response in ai_response]
    score = 0

    say(f"Let's start the trivia game about {subject}!")

    # Thread target for fetching follow-up questions
    def fetch_follow_up():
        nonlocal follow_up_response
        follow_up_response = get_trivia_questions(
            subject, number_of_questions=TOTAL_QUESTIONS - 1
        )

    follow_up_response = None
    follow_up_questions_thread = threading.Thread(target=fetch_follow_up)

    follow_up_questions_thread.start()

    score = ask_question(questions[0], answer_choices[0], answers[0], 0, score)
    follow_up_questions_thread.join()
    if follow_up_response:
        questions.extend([response["question"] for response in follow_up_response])
        answer_choices.extend(
            [response["answerChoices"] for response in follow_up_response]
        )
        answers.extend([response["answer"] for response in follow_up_response])

    for i, question in enumerate(questions):
        if i == 0 or i >= TOTAL_QUESTIONS:
            continue
        score = ask_question(question, answer_choices[i], answers[i], i, score)

    say(f"Game Over! You scored {score} out of {TOTAL_QUESTIONS}.")
    if score >= WIN_TOTAL:
        is_winner = input("Dispense?")
        if is_winner.lower() in ["yes", "y"]:
            say("Congratulations! You won the game!", rate=DEFAULT_RATE + 20)
            win()


if __name__ == "__main__":
    # You can change 'llama3' to any other model you have pulled (e.g., 'mistral', 'codellama', 'phi')
    while True:
        input("Press Enter to start the trivia game...")
        run_trivia_game()
