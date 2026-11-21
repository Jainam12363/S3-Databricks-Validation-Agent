
from src.agent.validation_agent import run_agent


def main():
    print("\n" + "=" * 55)
    print("       DATA VALIDATION & RECONCILIATION AGENT")
    print("=" * 55)

    print("\nLLM Provider : Groq")
    print("Model        : openai/gpt-oss-20b")
    print("Source       : AWS S3")
    print("Target       : Databricks")

    print("\nAgent initialized successfully.")
    print("Enter your questions below.")
    print("Type 'exit' or 'quit' to stop the agent.")

    conversation_history = None

    while True:
        try:
            user_message = input("\nYou: ").strip()

            if not user_message:
                continue

            if user_message.lower() in ["exit", "quit"]:
                print("\nAgent session ended.")
                break

            response, conversation_history = run_agent(
                user_message,
                conversation_history
            )

            print("\nAgent:")
            print(response)

        except KeyboardInterrupt:
            print("\n\nAgent session interrupted.")
            break

        except Exception as error:
            print("\nAn error occurred:")
            print(error)


if __name__ == "__main__":
    main()
