from dotenv import load_dotenv

from agent import ReActAgent


QUESTIONS = [
    "What fraction of Japan's population is Taiwan's population as of 2025?",
    "Compare the main display specs of iPhone 15 and Samsung S24.",
    "Who is the CEO of the startup 'Morphic' AI search?",
]


def main() -> None:
    load_dotenv()

    # IMPORTANT: use the SAME agent instance for all tasks, as required by the assignment.
    agent = ReActAgent(model="gpt-4o-mini", max_steps=5, temperature=0.2, verbose=True)

    print("\nRunning all assignment questions with one shared ReActAgent instance...\n")
    for i, question in enumerate(QUESTIONS, start=1):
        answer = agent.execute(question)
        print("\n" + "#" * 80)
        print(f"Task {i} final returned answer:")
        print(answer)
        print("#" * 80 + "\n")


if __name__ == "__main__":
    main()
