import google.generativeai as palm
import gradio as gr
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
import os
from dotenv import load_dotenv
import ast

# Load environment variables from .env file
load_dotenv()

# Configure the API key
api_key = os.getenv('Palm_Key')
palm.configure(api_key=api_key)

# List and select the model
models = [m for m in palm.list_models() if 'generateText' in m.supported_generation_methods]
model = models[0].name

# Function to highlight code
def format_code_with_syntax_highlighting(code, language):
    try:
        lexer = get_lexer_by_name(language.lower())
    except Exception as e:
        return f"Error in syntax highlighting: {e}"
    
    formatter = HtmlFormatter()
    return highlight(code, lexer, formatter)

# Define code quality metrics function
def calculate_code_quality_metrics(code):
    try:
        tree = ast.parse(code)
        num_lines = len(code.splitlines())
        num_nodes = len(list(ast.walk(tree)))
        num_functions = sum(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))
        cyclomatic_complexity = num_functions * 2

        metrics = {
            "Number of Lines": num_lines,
            "Number of AST Nodes": num_nodes,
            "Number of Functions": num_functions,
            "Cyclomatic Complexity (Approximate)": cyclomatic_complexity
        }
        return metrics
    except Exception as e:
        return f"Error in analyzing code quality: {e}"

# Enhanced example explanations
sample_code_explanations = """
----------------------------
Example 1: Python Code Snippet
def multiply_elements(lst, factor):
    return [x * factor for x in lst]

numbers = [1, 2, 3, 4]
result = multiply_elements(numbers, 3)
print(result)
Correct output: [3, 6, 9, 12]
Code Explanation: The function `multiply_elements` multiplies each element in the list `lst` by the given `factor`. The list comprehension `[x * factor for x in lst]` creates a new list with each element multiplied by `factor`. In this case, each number in `numbers` is multiplied by `3`, resulting in `[3, 6, 9, 12]`.
-----------------------------

Example 2: Python Code Snippet
def filter_even_numbers(nums):
    return [num for num in nums if num % 2 == 0]

values = [10, 15, 20, 25, 30]
filtered = filter_even_numbers(values)
print(filtered)
Correct output: [10, 20, 30]
Code Explanation: The function `filter_even_numbers` filters out the odd numbers from the list `nums`, returning only the even numbers. The list comprehension `[num for num in nums if num % 2 == 0]` includes only numbers divisible by `2`. Thus, from the list `values`, the even numbers `[10, 20, 30]` are returned.
------------------------------
"""


def generate_completion(code_section, language, detail_depth, req_type):
    prompt = f"""
    Your task is to act as a {language} Code {req_type}.
    I'll give you a Code Snippet.
    Your job is to {('explain the Code Snippet step-by-step' if req_type == 'Explainer' else 'provide refactoring suggestions and improvements' if req_type == 'Refactoring' else 'generate unit test cases for the code' if req_type == 'Unit Test Cases' else 'provide code quality metrics')}.
    Break down the code into as many steps as possible.
    Share intermediate checkpoints & steps along with results.
    Explanation detail level: {detail_depth}
    Few good examples of {language} code output between #### separator:
    ####
    {sample_code_explanations}
    ####
    Code Snippet is shared below, delimited with triple backticks:
    ```
    {code_section}
    ```
    """
    
    try:
        completion = palm.generate_text(
            model=model,
            prompt=prompt,
            temperature=0,
            max_output_tokens=500,
        )
        response = completion.result
        if not response:
            return "Unable to generate output. Try a different code snippet"
        return response
    except Exception as e:
        return f"An error occurred: {e}"

# Custom processing function to add syntax highlighting
def process_function(code_section, language, detail_depth, req_type):
    if req_type == "Code Quality Metrics":
        metrics = calculate_code_quality_metrics(code_section)
        formatted_code = format_code_with_syntax_highlighting(code_section, language)
        return formatted_code, metrics
    else:    
        response = generate_completion(code_section, language, detail_depth, req_type)
        formatted_code = format_code_with_syntax_highlighting(code_section, language)
        return formatted_code, response

# Define app UI with Gradio
iface = gr.Interface(
    fn=process_function,
    inputs=[
        gr.Textbox(label="Insert Code Snippet", lines=10, placeholder="Paste your code snippet here..."),
        gr.Dropdown(label="Select Programming Language", choices=["python", "java", "javascript"], value="python"),
        gr.Radio(label="Explanation Detail Level", choices=["Brief", "Detailed"], value="Detailed"),
        gr.Radio(label="Request Type", choices=["Explainer", "Refactoring", "Unit Test Cases", "Code Quality Metrics"], value="Explainer")
    ],
    outputs=[
        gr.HTML(label="Formatted Code Snippet"),
        gr.Textbox(label="Response", lines=20)
    ],
    title="Code Explainer, Refactoring Suggestions, Unit Test Cases Generator and Code Quality Metrics using Palm model",
    description="Paste a code snippet, select the programming language, explanation detail level, and request type",
    examples=[
        ["x = [1,2,3,4,5]\ny = [i*i for i in x if i%2==0]\nprint(y)", "python", "Detailed", "Explainer"],
        ["import math\n\n" "def calculate_area(radius):\n" "  return math.pi * radius * radius\n\n" "radius_list = [3, 5, 7]\n" "area_list = list(map(calculate_area, radius_list))\n" "print(area_list)", "python", "Detailed", "Refactoring"],
        ["def add(a, b):\n  return a + b", "python", "Detailed", "Unit Test Cases"],
        ["def add(a, b):\n  return a + b", "python", "Detailed", "Code Quality Metrics"]
    ]
)

iface.launch(share=True, debug=True)
