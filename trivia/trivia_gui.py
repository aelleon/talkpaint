import tkinter as tk

class TriviaGUI:
    def __init__(self, question, choices, correct_answer, user_answers, score):
        self.window = tk.Tk()
        self.window.title("Trivia Game")
        self.window.geometry("400x300")
        self.answer = None
        self.answered = threading.Event()
        self.correct_answer = correct_answer
        self.user_answers = user_answers
        self.score_ref = score

        tk.Label(self.window, text=question, wraplength=350, font=("Helvetica", 14)).pack(pady=20)
        for i, choice in enumerate(choices):
            btn = tk.Button(
                self.window,
                text=f"{chr(65+i)}. {choice}",
                width=30,
                command=lambda c=choice: self.select_answer(c)
            )
            btn.pack(pady=5)

        self.window.after(QUESTION_TIMEOUT * 1000, self.time_up)

    def select_answer(self, selected):
        self.answer = selected
        self.answered.set()
        self.window.destroy()

    def time_up(self):
        if not self.answered.is_set():
            self.window.destroy()

    def run(self):
        self.window.mainloop()
        self.answered.wait()
        if self.answer is None:
            say("Time's up! You didn't answer in time.")
            say(f"The correct answer was: {self.correct_answer}")
            self.user_answers.append("")
        else:
            self.user_answers.append(self.answer)
            if self.answer.lower() == self.correct_answer.lower():
                say("Correct!")
                self.score_ref += 1
            else:
                say(f"Wrong! The correct answer was: {self.correct_answer}")
