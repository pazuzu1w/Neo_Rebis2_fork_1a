class Agent:
    def __init__(self, chat):
        self.chat = chat

    def set_goal(self, goal):
        self.goal = goal

    def run(self):
        print("Agent running!")
        print(f"My goal is: {self.goal}")

        # Basic Planning
        print("Planning steps...")
        plan = ["Step 1: Understand the goal.", "Step 2: ???", "Step 3: Profit!"]
        for step in plan:
            print(f"- {step}")

        print("Executing plan...")