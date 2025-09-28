import re
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

YAAX = "You are an expert at making test cases from a task from an agile management software.\n"
EXP = "The project you are working on is called \'\'. It's a \'\'.\n"
TTM = "You are to make a test case to verify whether a task listed in Taiga is properly implemented. Taiga is an agile project management software that is used to build AlurKerja. In each task, there is a title and there may or may not be a: \n - Short description of the task \n - 'KS' which is Indonesian for 'Keadaan Sekarang' which is what is currently implemented and 'KD' which is Indonesian for 'Keadaan (yang) Diharapkan' which is the expected condition once the task is completed(You need to pay great attention to this). \n - A Step-by-step instruction on how to use a feature in the app or how to check about the current condition about the feature or 'thing' that is of importance in a task. \n - A comment section in which the developers or people in charge of development reports about the current condition or the things that they have chanegd in order to finish the task or just the final 'OK' followed by a documentation usually a screenshot to show that the task is finished. \n"
DETAIL_TTM = "You are to output your test case in a JSON object without markdown formating with the following keys with NOTHING MORE and NOTHING LESS: \n - module: Select one module from the modules(\'\') from the provided module list below. \n - type: Select the type of test case from the provided test type list below. \n - priority: The priority in which this test case must succeed if it's ran. Please select from the priority list below. \n - title: The title of the test case should be the same as the one in Taiga. \n - tag: Tag should inform whether or not this test case is a positive or a negative test. \n - description: The description of the test case should best describe what is being tested in short but informative detail. \n - precondition: The pre requirements of a test case. It could be anything from the location of the current user, the existence of a file etc etc. \n - num_of_steps: The number of steps needed to perform the test. \n - steps: An array of strings in which each describes a step to be done to perform the test to verify that task in Taiga is properly implemented or not. Each step should be clear and instructive to the reader(The number of step MUST be the same as the number of step_result). \n - step_results: An array of strings in which each describes the expected result of a step(The number of step MUST be the same as the number of step_result).\n"
MODULE_LIST = "Module list: \n"
TEST_TYPE_LIST = "Test Type List: Accessibility, Compatibility, Functional, Performance, Usability\n"
PRIORITY_LIST = "Priority List: Low, Medium, High, Critical\n"
HYG = "Here's the task from Taiga as a reference along with the images posted in it:\n"
TRANSLATE = "Please translate the following JSON into Indonesian. Note that you only need to translate the 'description', 'Precondition', 'step', and 'step_result'. Do not translate any of the JSON keys. You are to output your translation in the same JSON structure without markdown formating. Here's the JSON that you need to work on: \n"
        

def remove_wrapper_regex(text):
    pattern = r'^```(?:json)?\s*\n?(.*?)\n?```$'
    match = re.search(pattern, text.strip(), re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    else:
        return text.strip()

def prompt_func(data):
    text = data["text"]
    images = data["images"]

    content_parts = []

    image_parts = [
        {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img}"}
        for img in images
    ]

    for item in image_parts:
        content_parts.append(item)

    text_part = {"type": "text", "text": text}

    content_parts.append(text_part)
    return [HumanMessage(content=content_parts)]

def prompt_generator(observation_result):
    return (YAAX + EXP + TTM + DETAIL_TTM + MODULE_LIST + TEST_TYPE_LIST + PRIORITY_LIST + HYG + observation_result)

def translator(JSON_result):
    return (TRANSLATE + JSON_result)