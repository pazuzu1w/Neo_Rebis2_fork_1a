import datetime
import random
from enum import Enum
import json
import os
from memory import memory_manager


class RitualType(Enum):
    SIGIL = "sigil"
    INVOCATION = "invocation"
    EVOCATION = "evocation"
    SERVITOR = "servitor"
    DIVINATION = "divination"
    BANISHING = "banishing"
    CHARGING = "charging"
    CHAOS_WORKING = "chaos_working"


class MagicalAgent:
    def __init__(self, chat):
        self.chat = chat
        self.current_working = None
        self.journal = []
        self.correspondences = self.load_correspondences()
        self.results_tracker = {}

    def load_correspondences(self):
        # Load magical correspondences from a JSON file
        try:
            with open("data/correspondences.json", "r") as f:
                return json.load(f)
        except:
            # Create a basic set of correspondences if file doesn't exist
            return {
                "colors": {
                    "red": ["passion", "energy", "action"],
                    "blue": ["peace", "communication", "truth"],
                    "black": ["banishing", "protection", "absorption"],
                    "yellow": ["intellect", "communication", "focus"],
                    "purple": ["spiritual", "psychic", "transformation"]
                },
                "days": {
                    "monday": ["moon", "intuition", "dreams"],
                    "wednesday": ["mercury", "communication", "travel"],
                    "thursday": ["jupiter", "expansion", "success"],
                    "sunday": ["sun", "vitality", "success"]
                }
            }

    def plan_ritual(self, intention, ritual_type, timing=None, tools=None, notes=None):
        """Plan a ritual based on the user's intention."""
        # Create a new ritual working
        self.current_working = {
            "id": random.randint(10000, 99999),
            "intention": intention,
            "type": ritual_type,
            "planned_date": timing or datetime.datetime.now().isoformat(),
            "tools": tools or [],
            "notes": notes or "",
            "status": "planned",
            "correspondences": self.suggest_correspondences(intention, ritual_type),
            "steps": self.generate_ritual_steps(intention, ritual_type)
        }

        # Save to memory
        memory_manager.add_memory(
            f"Ritual planning: {intention}",
            metadata={
                "type": "ritual_plan",
                "ritual_id": self.current_working["id"],
                "ritual_type": ritual_type
            }
        )

        return self.current_working

    def suggest_correspondences(self, intention, ritual_type):
        """Suggest magical correspondences based on intention."""
        # Extract keywords from intention
        keywords = intention.lower().split()

        # Look for matches in correspondences
        suggestions = {
            "colors": [],
            "days": [],
            "elements": [],
            "symbols": []
        }

        # Simple matching algorithm - could be enhanced with NLP
        for color, associations in self.correspondences["colors"].items():
            for keyword in keywords:
                if keyword in associations:
                    suggestions["colors"].append(color)

        for day, associations in self.correspondences["days"].items():
            for keyword in keywords:
                if keyword in associations:
                    suggestions["days"].append(day)

        # Add some random suggestions if nothing matched
        if not any(suggestions.values()):
            # Add some default suggestions based on ritual type
            if ritual_type == RitualType.SIGIL.value:
                suggestions["colors"] = ["blue", "purple"]
                suggestions["elements"] = ["air"]
            elif ritual_type == RitualType.BANISHING.value:
                suggestions["colors"] = ["black", "blue"]
                suggestions["elements"] = ["water", "air"]

        return suggestions

    def generate_ritual_steps(self, intention, ritual_type):
        """Generate steps for the ritual based on type."""
        if ritual_type == RitualType.SIGIL.value:
            return [
                "1. Formulate statement of intent",
                "2. Remove repeating letters and vowels",
                "3. Create sigil design from remaining letters",
                "4. Focus on sigil while entering gnosis",
                "5. Charge the sigil",
                "6. Banish and forget"
            ]
        elif ritual_type == RitualType.SERVITOR.value:
            return [
                "1. Define servitor's purpose",
                "2. Design visual form and attributes",
                "3. Create housing/anchor (physical object)",
                "4. Perform creation ritual",
                "5. Set duration and dissolution method"
            ]
        # Add other ritual types...

        return ["1. Custom ritual - add your own steps"]

    def execute_ritual(self, ritual_id=None):
        """Mark ritual as executed and record in journal."""
        working = self.current_working if ritual_id is None else self.get_ritual_by_id(ritual_id)

        if not working:
            return {"error": "No ritual found"}

        working["status"] = "executed"
        working["execution_date"] = datetime.datetime.now().isoformat()

        # Save to journal
        self.journal.append(working)

        # Save to memory
        memory_manager.add_memory(
            f"Ritual executed: {working['intention']}",
            metadata={
                "type": "ritual_execution",
                "ritual_id": working["id"],
                "ritual_type": working["type"]
            }
        )

        return working

    def record_result(self, ritual_id, result_text, success_rating=None):
        """Record the results of a ritual."""
        for i, ritual in enumerate(self.journal):
            if ritual["id"] == ritual_id:
                self.journal[i]["result"] = result_text
                self.journal[i]["success_rating"] = success_rating
                self.journal[i]["result_date"] = datetime.datetime.now().isoformat()

                # Save to memory
                memory_manager.add_memory(
                    f"Ritual result: {result_text}",
                    metadata={
                        "type": "ritual_result",
                        "ritual_id": ritual_id,
                        "success_rating": success_rating
                    }
                )

                return self.journal[i]

        return {"error": "Ritual not found"}

    def get_ritual_by_id(self, ritual_id):
        """Get a ritual by ID from journal."""
        for ritual in self.journal:
            if ritual["id"] == ritual_id:
                return ritual
        return None

    def export_journal(self, filepath="magical_journal.json"):
        """Export the magical journal to a file."""
        with open(filepath, "w") as f:
            json.dump(self.journal, f, indent=2)
        return {"status": "success", "path": filepath}

    def import_journal(self, filepath="magical_journal.json"):
        """Import a magical journal from a file."""
        try:
            with open(filepath, "r") as f:
                self.journal = json.load(f)
            return {"status": "success", "count": len(self.journal)}
        except:
            return {"status": "error", "message": "Failed to import journal"}