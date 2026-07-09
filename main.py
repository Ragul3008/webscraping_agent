from agent.planner import Planner


def main():

    print("\nLLM-Controlled Autonomous Dataset Finder\n")

    topic = input("Enter topic: ").strip()

    planner = Planner()

    planner.execute(topic)


if __name__ == "__main__":
    main()