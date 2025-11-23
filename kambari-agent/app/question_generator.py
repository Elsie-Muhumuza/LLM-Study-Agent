import os
import json
import random
from typing import List, Dict, Optional, Tuple
import google.generativeai as genai
from pathlib import Path

# Configure Google's Generative AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")

genai.configure(api_key=GEMINI_API_KEY)

# Initialize the model
model = genai.GenerativeModel('gemini-pro')

# Default prompts for question generation with emojis and formatting
DEFAULT_PROMPTS = {
    "application": """Generate 2-3 thought-provoking application questions for a Bible study on {passage}.
    Focus on how the passage applies to modern life and personal faith journey.
    Start each question with an appropriate emoji and ensure they're engaging and practical.
    Format as a JSON array of strings.
    
    Example format:
    [
        "🔍 What practical steps can we take from {passage} to improve our daily walk with God?",
        "💡 How might applying {passage} change your approach to [specific situation] this week?"
    ]""",
    
    "discussion": """Generate 3-4 open-ended discussion questions for a Bible study on {passage}.
    These should encourage group discussion and different perspectives.
    Start each question with an appropriate emoji and make them thought-provoking.
    Format as a JSON array of strings.
    
    Example format:
    [
        "🤔 What stands out to you most in {passage} and why?",
        "💭 How might someone with a different background interpret this passage?"
    ]""",
    
    "reflection": """Create 1-2 deep reflection questions about {passage}.
    These should help individuals connect the passage to their personal spiritual growth.
    Start each with a meaningful emoji and make them introspective.
    Format as a JSON array of strings.
    
    Example format:
    [
        "💬 What is God saying to you personally through {passage}?",
        "🌱 How can you apply the truth of {passage} to grow in your spiritual journey this week?"
    ]"""
}

def generate_questions(passage_reference: str, question_type: str, custom_prompt: Optional[str] = None) -> List[str]:
    """
    Generate study questions using Google's Gemini API.
    
    Args:
        passage_reference: Bible passage reference (e.g., "John 3:16-17")
        question_type: Type of questions to generate (application, discussion, reflection)
        custom_prompt: Optional custom prompt to override the default
        
    Returns:
        List of generated questions
    """
    try:
        # Use custom prompt if provided, otherwise use default
        prompt = custom_prompt or DEFAULT_PROMPTS.get(question_type, '')
        if not prompt:
            raise ValueError(f"Invalid question type: {question_type}")
        
        # Format the prompt with the passage reference
        formatted_prompt = prompt.format(passage=passage_reference)
        
        # Generate response using Gemini
        response = model.generate_content(
            formatted_prompt,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": 1024,
            },
        )
        
        # Parse the response (expecting JSON array of strings)
        try:
            questions = json.loads(response.text.strip())
            if not isinstance(questions, list):
                questions = [q.strip() for q in response.text.split('\n') if q.strip()]
        except json.JSONDecodeError:
            # Fallback: Try to extract questions from plain text
            questions = [q.strip() for q in response.text.split('\n') if q.strip() and len(q.strip()) > 10]
        
        return questions[:5]  # Return max 5 questions
        
    except Exception as e:
        print(f"Error generating questions: {str(e)}")
        # Fallback to default questions if API call fails
        return get_fallback_questions(passage_reference, question_type)

def get_fallback_questions(passage_reference: str, question_type: str) -> List[str]:
    """Generate simple fallback questions when API is unavailable."""
    base_questions = {
        "application": [
            f"How can you apply the message of {passage_reference} in your daily life?",
            f"What changes might {passage_reference} inspire you to make?",
        ],
        "discussion": [
            f"What stands out to you most in {passage_reference} and why?",
            f"How does {passage_reference} challenge your current understanding?",
            f"What questions does {passage_reference} raise for you?",
            # Permanent questions that will always be included
            "🙏 What does this passage teach us about God?",
            "👥 What does this passage teach us about man?"
        ],
        "reflection": [
            f"How does {passage_reference} speak to your current life situation?",
            f"What is God saying to you through {passage_reference}?",
        ]
    }
    return base_questions.get(question_type, [f"What are your thoughts on {passage_reference}?"])

def get_permanent_questions(passage_reference: str) -> List[str]:
    """
    Get the permanent questions that should be included with every study guide.
    These are designed to be thought-provoking and help with deeper understanding.
    
    Args:
        passage_reference: Bible passage reference (for context in the questions)
        
    Returns:
        List of permanent questions with emojis and formatting
    """
    return [
        f"🌌 **Divine Nature**: What does {passage_reference} reveal about God's character and nature?",
        f"👥 **Human Condition**: How does {passage_reference} help us understand humanity's relationship with God?",
        f"💡 **Key Truth**: What is the most important spiritual truth we should take away from {passage_reference}?",
        f"🔄 **Transformation**: How should {passage_reference} change the way we live our daily lives?"
    ]

def generate_study_guide(passage_reference: str, theme: str = "") -> Dict[str, List[str]]:
    """
    Generate a complete study guide for a Bible passage.
    
    Args:
        passage_reference: Bible passage reference
        theme: Optional theme or topic to focus on
        
    Returns:
        Dictionary containing different types of questions
    """
    # Generate regular questions
    application_questions = generate_questions(passage_reference, "application")
    discussion_questions = generate_questions(passage_reference, "discussion")
    reflection_questions = generate_questions(passage_reference, "reflection")
    
    # Get permanent questions
    permanent_questions = get_permanent_questions(passage_reference)
    
    # Combine reflection questions with permanent questions at the end
    combined_reflection = reflection_questions + permanent_questions
    
    study_guide = {
        "application": application_questions,
        "discussion": discussion_questions,
        "reflection": combined_reflection,  # Includes permanent questions at the end
        "theme": theme,
        "passage": passage_reference
    }
    
    return study_guide

def save_study_guide(study_guide: Dict, output_dir: str = "study_guides") -> str:
    """
    Save a study guide to a JSON file.
    
    Args:
        study_guide: The study guide dictionary to save
        output_dir: Directory to save the file in
        
    Returns:
        Path to the saved file
    """
    os.makedirs(output_dir, exist_ok=True)
    safe_title = "".join(c if c.isalnum() else "_" for c in study_guide["passage"])
    filename = f"{output_dir}/study_guide_{safe_title}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(study_guide, f, indent=2)
    
    return filename

if __name__ == "__main__":
    # Example usage
    passage = "John 3:16-17"
    print(f"Generating study guide for {passage}...")
    guide = generate_study_guide(passage, "God's Love and Salvation")
    saved_path = save_study_guide(guide)
    print(f"Study guide saved to: {saved_path}")