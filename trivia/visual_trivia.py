import time
import ollama
import subprocess
import json
import threading
import cv2

MODEL_TO_USE = "gemma3:latest"
DEFAULT_RATE = 180  # Default speech rate for TTS
TOTAL_QUESTIONS = 5
BOX_LOCATIONS = [(100, 100), (1000, 1000), (50, 300), (300, 300) ]
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

    initial_prompt = (
        f"Generate {number_of_questions} new multiple-choice questions about '{subject}' that gradually get harder. "
        "Make answers choices as only one word or short phrases."
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
        clean_json = response_text.strip("`").split("\n", 1)[1].rsplit("\n", 1)[0]
        questions = json.loads(clean_json)
        return questions
    except json.JSONDecodeError:
        print("Error decoding JSON response from AI")
        if retry_count > 0:
            print(f"{retry_count} retries left")
            print("Retrying to get trivia questions...")
            return get_trivia_questions(subject, retry_count - 1)


def ask_question(question, answer_choices, answer, question_number, score):
    global image
    # Create a clean copy of the background image for this question
    image = cv2.imread("background.png")
    if image is None:
        print("Error: Could not load background.png")
        return

    question_number = question_number + 1
    question_str = f"\nQuestion {question_number}: {question}"
    # Draw the question at the top of the image
    cv2.putText(image, question, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.imshow("Trivia Game", image)
    cv2.waitKey(1)  # Allow the image to be displayed

    say(question_str)

    for j, choice in enumerate(answer_choices):
        cv2.putText(
            image,
            f"{choice}",
            BOX_LOCATIONS[j],
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            (0, 0, 255),
            2,
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
            color = (0, 255, 0) if j == selected_index else (0, 0, 255)  # Green if selected, red otherwise
            cv2.putText(
                display_image,
                f"{choice}",
                BOX_LOCATIONS[j],
                cv2.FONT_HERSHEY_SIMPLEX,
                1.5,
                color,
                2,
            )
        
        # Calculate remaining time and bar width
        elapsed = currentTime - startTime
        remaining_ratio = 1 - (elapsed / timeout)
        current_bar_width = int(bar_width * remaining_ratio)
        
        # Draw the timer bar
        cv2.rectangle(display_image, (20, bar_y), (20 + bar_width, bar_y + bar_height), (100, 100, 100), -1)  # Background bar
        cv2.rectangle(display_image, (20, bar_y), (20 + current_bar_width, bar_y + bar_height), (0, 255, 0), -1)  # Time remaining
        
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

    ask_question(questions[0], answer_choices[0], answers[0], 0, score)
    follow_up_questions_thread.join()
    if follow_up_response:
        questions.extend([response["question"] for response in follow_up_response])
        answer_choices.extend(
            [response["answerChoices"] for response in follow_up_response]
        )
        answers.extend([response["answer"] for response in follow_up_response])

    for i, question in enumerate(questions):
        if i == 0:
            continue
        ask_question(question, answer_choices[i], answers[i], i, score)

    say(f"Game Over! You scored {score} out of {len(questions)}.")


if __name__ == "__main__":
    # You can change 'llama3' to any other model you have pulled (e.g., 'mistral', 'codellama', 'phi')
    while True:
        input("Press Enter to start the trivia game...")
        run_trivia_game()
