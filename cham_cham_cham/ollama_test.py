import ollama
import subprocess

def simple_generation(model_name="llama3", prompt="Why is the sky blue?"):
    """
    Performs a simple text generation with a given model and prompt.
    """
    print(f"\n--- Simple Generation with {model_name} ---")
    try:
        response = ollama.generate(model=model_name, prompt=prompt)
        print(f"Prompt: {prompt}")
        print(f"Response: {response['response']}")
    except ollama.ResponseError as e:
        print(f"Error: {e.error}")
        if e.status_code == 404:
            print(f"Model '{model_name}' not found. Please run 'ollama pull {model_name}' first.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def streaming_chat(model_name="llama3", initial_message="Tell me a short story about a brave knight."):
    """
    Demonstrates streaming responses for a chat-like interaction.
    """
    print(f"\n--- Streaming Chat with {model_name} ---")
    messages = [{'role': 'user', 'content': initial_message}]

    print(f"User: {initial_message}")
    print("AI (streaming): ", end="", flush=True)

    try:
        full_response_content = ""
        for chunk in ollama.chat(model=model_name, messages=messages, stream=True):
            if chunk['message']['content']:
                print(chunk['message']['content'], end="", flush=True)
                full_response_content += chunk['message']['content']
        print("\n") # New line after the streamed response

        messages.append({'role': 'assistant', 'content': full_response_content})
        return messages # Return updated messages for continued conversation

    except ollama.ResponseError as e:
        print(f"Error during streaming: {e.error}")
        if e.status_code == 404:
            print(f"Model '{model_name}' not found. Please run 'ollama pull {model_name}' first.")
        return []
    except Exception as e:
        print(f"An unexpected error occurred during streaming: {e}")
        return []

def interactive_chat(model_name="llama3"):
    messages = []
    # Add the system message to define the model's persona
    system_prompt = "You are a trivia host. Please ask the user what topic they would like trivia about, then generate an easy question based on that topic that has a short answer, then evaluate their response leniently to determine if they are correct or not."
    messages.append({'role': 'system', 'content': system_prompt})
    print(f"System: {system_prompt}")

    # Initial prompt to the model to start the trivia game
    initial_user_message = "Start the trivia game by asking me for a topic."
    messages.append({'role': 'user', 'content': initial_user_message})

    print("AI: ", end="", flush=True)
    initial_ai_response_content = ""
    try:
        # Get the AI's initial response (asking for a topic)
        for chunk in ollama.chat(model=model_name, messages=messages, stream=True):
            if chunk['message']['content']:
                print(chunk['message']['content'], end="", flush=True)
                initial_ai_response_content += chunk['message']['content']
        print("\n") # New line after AI's initial response
        messages.append({'role': 'assistant', 'content': initial_ai_response_content})
    except ollama.ResponseError as e:
        print(f"\nError during initial chat setup: {e.error}")
        if e.status_code == 404:
            print(f"Model '{model_name}' not found. Please run 'ollama pull {model_name}' first.")
        return # Exit if initial setup fails
    except Exception as e:
        print(f"\nAn unexpected error occurred during initial chat setup: {e}")
        return # Exit if initial setup fails

    while True:
        user_input = input("You: ")

        if user_input.lower() in ["quit", "exit"]:
            print("Exiting chat. Goodbye!")
            break
        elif user_input.lower() == "reset":
            messages = [{'role': 'system', 'content': system_prompt}] # Reset to just the system prompt
            print("Conversation history cleared.")
            continue

        messages.append({'role': 'user', 'content': user_input})

        print("AI: ", end="", flush=True)
        current_response_content = ""
        try:
            for chunk in ollama.chat(model=model_name, messages=messages, stream=True):
                if chunk['message']['content']:
                    print(chunk['message']['content'], end="", flush=True)
                    current_response_content += chunk['message']['content']
            print("\n") # New line after AI's response
            subprocess.call(['say', current_response_content])
            messages.append({'role': 'assistant', 'content': current_response_content})
        except ollama.ResponseError as e:
            print(f"\nError: {e.error}")
            if e.status_code == 404:
                print(f"Model '{model_name}' not found. Please run 'ollama pull {model_name}' first.")
            # Remove the last user message if there was an error, so it doesn't pollute history
            messages.pop()
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")
            messages.pop() # Remove the last user message

if __name__ == "__main__":
    # You can change 'llama3' to any other model you have pulled (e.g., 'mistral', 'codellama', 'phi')
    MODEL_TO_USE = "gemma3:latest" 

    # --- Example 1: Simple Generation ---
    # simple_generation(MODEL_TO_USE, "Tell me a fun fact about space.")

    # # --- Example 2: Streaming Chat ---
    # # The 'streaming_chat' function returns the updated message history
    # conversation_history = streaming_chat(MODEL_TO_USE, "Can you tell me more about that knight's next adventure?")
    # if conversation_history:
    #     print("\n--- Current Conversation History (after streaming chat) ---")
    #     for msg in conversation_history:
    #         print(f"{msg['role'].capitalize()}: {msg['content']}")

    # --- Example 3: Interactive Chat ---
    interactive_chat(MODEL_TO_USE)