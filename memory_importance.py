# memory_importance.py
import re
from datetime import datetime


class MemoryImportanceScorer:
    def __init__(self, memory_manager, model_interface):
        self.memory_manager = memory_manager
        self.model_interface = model_interface
        self.importance_keywords = [
            "critical", "important", "remember", "key", "significant",
            "essential", "crucial", "vital", "remember this", "don't forget"
        ]

    def score_memory_importance(self, text, metadata=None):
        """Score a memory's importance from 0-100"""
        if not text:
            return 0

        base_score = 50  # Default importance

        # Factor 1: Keywords indicating importance
        keyword_score = self._calculate_keyword_score(text)

        # Factor 2: Emotional content
        emotion_score = self._calculate_emotion_score(text)

        # Factor 3: Information density
        info_density_score = self._calculate_info_density(text)

        # Factor 4: Recency (if timestamp available)
        recency_score = self._calculate_recency_score(metadata)

        # Factor 5: AI judgment of importance
        ai_importance_score = self._calculate_ai_importance(text)

        # Weighted combination
        final_score = (
                keyword_score * 0.2 +
                emotion_score * 0.15 +
                info_density_score * 0.2 +
                recency_score * 0.15 +
                ai_importance_score * 0.3
        )

        # Ensure score is between 0-100
        return max(0, min(100, final_score))

    def _calculate_keyword_score(self, text):
        """Calculate score based on importance keywords"""
        text_lower = text.lower()
        keyword_count = sum(1 for keyword in self.importance_keywords if keyword in text_lower)
        return min(100, keyword_count * 10)  # Up to 100 points

    def _calculate_emotion_score(self, text):
        """Calculate score based on emotional content"""
        # This is a simplified version - you might want to use a sentiment analysis library
        emotion_keywords = ["love", "hate", "happy", "sad", "angry", "excited", "afraid"]
        text_lower = text.lower()
        emotion_count = sum(1 for keyword in emotion_keywords if keyword in text_lower)
        return min(100, emotion_count * 10)

    def _calculate_info_density(self, text):
        """Calculate score based on information density"""
        # Count entities like numbers, proper nouns, etc.
        number_count = len(re.findall(r'\d+', text))

        # Count capital words as potential proper nouns
        capital_words = len(re.findall(r'\b[A-Z][a-zA-Z]*\b', text))

        # Count total words
        total_words = len(text.split())

        if total_words == 0:
            return 0

        # Calculate density
        info_ratio = (number_count + capital_words) / total_words
        return min(100, info_ratio * 200)  # Scale to 0-100

    def _calculate_recency_score(self, metadata):
        """Calculate score based on recency"""
        if not metadata or "timestamp" not in metadata:
            return 50  # Default if no timestamp

        try:
            # Parse timestamp
            timestamp = datetime.fromisoformat(metadata["timestamp"])
            now = datetime.now()

            # Calculate days difference
            days_diff = (now - timestamp).days

            # Exponential decay: score = 100 * 0.9^days
            recency_score = 100 * (0.9 ** days_diff)
            return max(10, recency_score)  # Minimum score of 10
        except:
            return 50  # Default on error

    def _calculate_ai_importance(self, text):
        """Use the AI to judge importance"""
        prompt = f"""On a scale of 0-100, how important is the following information to remember?

        Text: {text}

        Provide only a numeric score from 0-100:"""

        response = self.model_interface.generate_text(prompt)

        # Try to extract a numeric score from the response
        match = re.search(r'\b(\d{1,3})\b', response)
        if match:
            score = int(match.group(1))
            return max(0, min(100, score))
        else:
            return 50  # Default if no clear number found