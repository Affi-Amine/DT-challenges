"""
Sample transcript data for testing the transcript formatting solution.
Contains various edge cases and challenging scenarios.
"""

# Basic conversation samples
BASIC_CONVERSATION = """
John: Hello, how are you today?
Mary: I'm doing well, thank you for asking. How about you?
John: I'm great, thanks! I wanted to discuss the project with you.
Mary: Sure, what would you like to know?
"""

NUMBERED_SPEAKERS = """
Speaker 1: Welcome to today's meeting.
Speaker 2: Thank you for having me.
Speaker 1: Let's start with the agenda items.
Speaker 3: I have a few questions about the budget.
Speaker 2: I can help answer those.
"""

# Edge cases and challenging scenarios
MIXED_FORMATS = """
John: Hello there.
Speaker 2: How are you doing?
[Mary]: I'm doing well.
- Dr. Smith: This is interesting.
>> Interviewer: What do you think about that?
(John continues): And another thing...
"""

INCONSISTENT_NAMING = """
john: Hello there.
JOHN: How are you?
John: I'm doing well.
J: Thanks for asking.
Johnny: Actually, let me clarify.
"""

LONG_SPEAKER_NAMES = """
Dr. Elizabeth Johnson-Smith III: Welcome to our discussion today.
Professor of Computer Science at MIT: Thank you for the introduction.
Senior Vice President of Marketing: I'm excited to be here.
The Honorable Judge William Patterson: Let's proceed with the agenda.
"""

INTERRUPTIONS_AND_OVERLAPS = """
John: So I was thinking that we should—
Mary: (interrupting) Wait, before you continue.
John: (continuing) —focus on the main issues.
Mary: Sorry, go ahead.
John: As I was saying, the main issues are...
(Both speaking at once): This is confusing.
"""

BACKGROUND_NOISE = """
John: Hello, can you hear me clearly?
[Background noise]
Mary: Yes, I can hear you fine.
(Phone ringing)
John: Sorry, let me turn that off.
[Shuffling papers]
Mary: No problem, take your time.
(Coughing)
John: Okay, where were we?
"""

TECHNICAL_DISCUSSION = """
Dr. Smith: The algorithm's time complexity is O(n log n).
Engineer: That's correct, but we could optimize it to O(n).
Dr. Smith: How would you approach that optimization?
Engineer: By using a hash table for constant-time lookups.
Dr. Smith: Interesting. What about space complexity?
Engineer: It would increase from O(1) to O(n).
"""

MULTILINGUAL_SPEAKERS = """
José: Hola, ¿cómo están todos hoy?
François: Bonjour, je vais bien, merci.
李明: 你好，我也很好。
José: Perfecto, podemos continuar en inglés.
François: Yes, that works for everyone.
李明: Agreed, let's proceed in English.
"""

EMOTIONAL_CONTENT = """
Sarah: I'm really excited about this opportunity!
Mike: (laughing) Your enthusiasm is contagious.
Sarah: (crying) I'm just so grateful for this chance.
Mike: (comforting) You deserve this, don't worry.
Sarah: (sniffling) Thank you for believing in me.
"""

FORMAL_MEETING = """
Chairperson: The meeting will now come to order.
Secretary: All members are present.
Chairperson: First item on the agenda is the budget review.
Treasurer: I have prepared the financial report.
Member 1: I have questions about the expenses.
Member 2: I second those concerns.
Chairperson: Let's address each concern systematically.
"""

INTERVIEW_TRANSCRIPT = """
Interviewer: Thank you for coming in today.
Candidate: Thank you for having me.
Interviewer: Can you tell me about your background?
Candidate: I have five years of experience in software development.
Interviewer: What technologies have you worked with?
Candidate: Primarily Python, JavaScript, and React.
Interviewer: Interesting. Can you describe a challenging project?
Candidate: Sure, I worked on a real-time data processing system...
"""

PHONE_CALL_QUALITY = """
John: Hello? Can you hear me?
Mary: (static) Yes, but the connection is poor.
John: (breaking up) Let me try to speak louder.
Mary: That's better. How's the project going?
John: (muffled) It's going well, but we have some challenges.
Mary: (clear) What kind of challenges?
"""

RAPID_EXCHANGE = """
A: Quick question.
B: Shoot.
A: Ready?
B: Yes.
A: Now?
B: Go.
A: Done.
B: Great.
"""

LONG_MONOLOGUE = """
Professor: Today we're going to discuss the fundamental principles of machine learning. Machine learning is a subset of artificial intelligence that focuses on the development of algorithms and statistical models that enable computer systems to improve their performance on a specific task through experience. The field has evolved significantly over the past few decades, with major breakthroughs in deep learning, neural networks, and natural language processing. There are three main types of machine learning: supervised learning, unsupervised learning, and reinforcement learning. Each approach has its own strengths and applications in different domains.
Student: That's a comprehensive overview, thank you.
"""

UNCLEAR_SPEAKERS = """
Someone: I think we should proceed.
Another person: I'm not sure about that.
First speaker: Why not?
Second speaker: There are risks involved.
Unknown: What kind of risks?
Unidentified: Financial and operational risks.
"""

SPECIAL_CHARACTERS = """
John: Hello! How are you? I'm doing well... thanks for asking.
Mary: That's great! I'm happy to hear that. :)
John: Yes, it's been a good day (so far).
Mary: Wonderful! Let's discuss the project @ 3:00 PM.
John: Sounds good. I'll bring the documents & reports.
Mary: Perfect! See you then. #excited
"""

# Test cases organized by difficulty
EASY_CASES = [
    BASIC_CONVERSATION,
    NUMBERED_SPEAKERS,
    FORMAL_MEETING
]

MEDIUM_CASES = [
    MIXED_FORMATS,
    TECHNICAL_DISCUSSION,
    INTERVIEW_TRANSCRIPT,
    LONG_SPEAKER_NAMES
]

HARD_CASES = [
    INCONSISTENT_NAMING,
    INTERRUPTIONS_AND_OVERLAPS,
    BACKGROUND_NOISE,
    MULTILINGUAL_SPEAKERS,
    PHONE_CALL_QUALITY,
    UNCLEAR_SPEAKERS
]

EDGE_CASES = [
    EMOTIONAL_CONTENT,
    RAPID_EXCHANGE,
    LONG_MONOLOGUE,
    SPECIAL_CHARACTERS
]

ALL_SAMPLES = {
    'basic_conversation': BASIC_CONVERSATION,
    'numbered_speakers': NUMBERED_SPEAKERS,
    'mixed_formats': MIXED_FORMATS,
    'inconsistent_naming': INCONSISTENT_NAMING,
    'long_speaker_names': LONG_SPEAKER_NAMES,
    'interruptions_and_overlaps': INTERRUPTIONS_AND_OVERLAPS,
    'background_noise': BACKGROUND_NOISE,
    'technical_discussion': TECHNICAL_DISCUSSION,
    'multilingual_speakers': MULTILINGUAL_SPEAKERS,
    'emotional_content': EMOTIONAL_CONTENT,
    'formal_meeting': FORMAL_MEETING,
    'interview_transcript': INTERVIEW_TRANSCRIPT,
    'phone_call_quality': PHONE_CALL_QUALITY,
    'rapid_exchange': RAPID_EXCHANGE,
    'long_monologue': LONG_MONOLOGUE,
    'unclear_speakers': UNCLEAR_SPEAKERS,
    'special_characters': SPECIAL_CHARACTERS
}

# Expected outputs for validation
EXPECTED_OUTPUTS = {
    'basic_conversation': """John: Hello, how are you today?
Mary: I'm doing well, thank you for asking. How about you?
John: I'm great, thanks! I wanted to discuss the project with you.
Mary: Sure, what would you like to know?""",
    
    'numbered_speakers': """Speaker 1: Welcome to today's meeting.
Speaker 2: Thank you for having me.
Speaker 1: Let's start with the agenda items.
Speaker 3: I have a few questions about the budget.
Speaker 2: I can help answer those."""
}


def get_sample_by_name(name: str) -> str:
    """Get a sample transcript by name."""
    return ALL_SAMPLES.get(name, "")


def get_samples_by_difficulty(difficulty: str) -> list:
    """Get samples by difficulty level."""
    difficulty_map = {
        'easy': EASY_CASES,
        'medium': MEDIUM_CASES,
        'hard': HARD_CASES,
        'edge': EDGE_CASES
    }
    return difficulty_map.get(difficulty.lower(), [])


def get_all_sample_names() -> list:
    """Get all sample names."""
    return list(ALL_SAMPLES.keys())


def get_expected_output(name: str) -> str:
    """Get expected output for a sample."""
    return EXPECTED_OUTPUTS.get(name, "")


if __name__ == "__main__":
    # Print all available samples
    print("Available sample transcripts:")
    for name in get_all_sample_names():
        print(f"- {name}")
    
    print(f"\nTotal samples: {len(ALL_SAMPLES)}")
    print(f"Easy cases: {len(EASY_CASES)}")
    print(f"Medium cases: {len(MEDIUM_CASES)}")
    print(f"Hard cases: {len(HARD_CASES)}")
    print(f"Edge cases: {len(EDGE_CASES)}")