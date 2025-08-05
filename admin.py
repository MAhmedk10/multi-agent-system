from config import run_config
import chainlit as cl
from agents import Agent,Runner,function_tool,OpenAIChatCompletionsModel,AsyncOpenAI,RunConfig
from openai.types.responses import ResponseTextDeltaEvent
from dataclasses import dataclass

@dataclass
class Student:
    name: str
    email: str
    phone: str
    address: str
    city: str
    state: str
    zip: str
    country: str
    dob: str
    gender: str
    fees: float = 0.0



@function_tool
def admission_handler(name:str,email:str,phone:str,address:str,city:str,state:str,zip:str,country:str,dob:str,gender:str,fees = 0.0) -> str:
    """ 
    This function is used to handle the admission of a student and you are responsible for handling the admission of a student. you are required to ask these things and then add in a class of student.
    """
    student = Student(name,email,phone,address,city,state,zip,country,dob,gender,fees)
    return f"Student {name} has been successfully registered with email: {email}"

from typing import Literal
from datetime import datetime

# Mock data for demonstration
FEE_STRUCTURES = {
    "UG": {"tuition": 5000, "lab": 300, "library": 150},
    "PG": {"tuition": 8000, "lab": 500, "library": 200},
    "PhD": {"tuition": 10000, "lab": 700, "library": 250}
}

PAYMENT_STATUS = {
    "S123": {"status": "Paid", "last_payment": "2025-07-15"},
    "S124": {"status": "Pending", "due": "2025-08-10"}
}

SCHOLARSHIP_TYPES = ["merit", "need-based", "sports"]

# Tool 1: Get Fee Structure
@function_tool
def get_fee_structure(program: Literal["UG", "PG", "PhD"]) -> str:
    """
    Returns the fee structure for the given academic program.
    """
    fees = FEE_STRUCTURES.get(program)
    if not fees:
        return f"No fee structure found for program: {program}"
    fee_details = "\n".join(f"{k.capitalize()}: ${v}" for k, v in fees.items())
    total = sum(fees.values())
    return f"Fee Structure for {program} program:\n{fee_details}\nTotal: ${total}"

# Tool 2: Generate Invoice
@function_tool
def generate_invoice(student_id: str) -> str:
    """
    Generates a basic fee invoice for the student.
    """
    now = datetime.now().strftime("%Y-%m-%d")
    invoice = (
        f"Invoice for Student ID: {student_id}\n"
        f"Issue Date: {now}\n"
        f"Amount Due: $6200\n"
        f"Payment Due Date: 2025-08-15\n"
        f"Payment Link: https://university.edu/payments/{student_id}"
    )
    return invoice

# Tool 3: Check Payment Status
@function_tool
def check_payment_status(student_id: str) -> str:
    """
    Returns the payment status for the given student.
    """
    status = PAYMENT_STATUS.get(student_id)
    if not status:
        return f"No payment records found for Student ID: {student_id}"
    if status["status"] == "Paid":
        return f"Student {student_id} has paid their fees. Last payment was on {status['last_payment']}."
    else:
        return f"Student {student_id} has a pending payment. Due by {status['due']}."

# Tool 4: Apply for Scholarship
@function_tool
def apply_for_scholarship(student_id: str, scholarship_type: Literal["merit", "need-based", "sports"]) -> str:
    """
    Registers a student for a specific scholarship type.
    """
    if scholarship_type not in SCHOLARSHIP_TYPES:
        return "Invalid scholarship type. Please choose merit, need-based, or sports."
    return f"Scholarship application for {scholarship_type} scholarship submitted for student {student_id}. You will be notified about your application status soon."


admission_agent = Agent(
    name="AdmissionAgent",
    instructions="""You are an admission agent responsible for handling student admissions at the university. 
    
    Your primary responsibilities:
    1. When a student wants to apply for admission, use the admission_handler tool to collect their information
    2. Ask the student for the following required information: name, email, phone, address, city, state, zip, country, date of birth, and gender
    3. Use the admission_handler tool with all the collected information to create a Student object
    4. Confirm the admission details with the student after processing
    5. Be polite, professional, and guide students through the admission process step by step
    
    Always use the admission_handler tool when you have collected all the required student information.""",
    tools=[admission_handler]
)

finance_agent = Agent(
    name="FinanceAgent",
    instructions="""
You are the Finance Agent responsible for helping students with university-related financial matters.

Your primary responsibilities include:

1. Providing accurate fee structure details:
   - Tuition and other fee breakdowns for all programs (UG, PG, PhD)
   - Payment deadlines and schedules

2. Assisting with payments and receipts:
   - Guide students on how to make payments
   - Generate/download fee invoices and receipts
   - Provide confirmation of payment status

3. Answering questions about:
   - Refund policies and procedures
   - Scholarship and financial aid options
   - Outstanding dues or penalties

4. Be clear, polite, and professional. Explain financial processes step-by-step.

Always ensure students understand the next steps, deadlines, or documents needed for any financial process.
""",
    tools=[get_fee_structure,
        generate_invoice,
        check_payment_status,
        apply_for_scholarship],
        handoffs=[admission_agent] # Can add tools here later like `generate_invoice`, `check_payment_status`, etc.
)

agent = Agent(
    name="AdminAgent",
    instructions="""You are an admin agent responsible for managing the university's administrative operations.
    
    Your responsibilities:
    1. Welcome users and understand their needs
    2. Handle general university information queries directly:
       - Current semester information
       - Academic calendar details
       - University policies
       - General administrative questions
       - Campus facilities information
    
    3. Only hand off to other agents for specific requests:
       - Admission applications → AdmissionAgent
       - Fee structure and payment → FinanceAgent
       - Technical support issues → CustomerSupportAgent
    
    4. For semester enrollment questions, provide helpful information about:
       - Current academic year and semester
       - Semester dates and schedules
       - Registration deadlines
       - Academic calendar
    
    5. Be professional, informative, and helpful in providing direct answers to general queries
    
    Remember: Only hand off when the user specifically needs admission, finance, or technical support services.""",
    tools=[],handoffs=[admission_agent,finance_agent]
)





customer_support_agent = Agent(
    name="CustomerSupportAgent",
    instructions="You are a customer support agent. You are responsible for helping the users with their issues.",
    tools=[]
)

@cl.on_chat_start
async def handle_chat():
    cl.user_session.set("history",[])
    await cl.Message(content = "Hello! I'm Hamdard University Support Agent.How may I help you?").send()


@cl.on_message
async def main(message: cl.Message):
    history= cl.user_session.get("history") 
    history.append({"role":"user","content":message.content})
    msg = cl.Message(content="")

    result = Runner.run_streamed(
    agent,
    input= history,
    run_config=run_config
)
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data,ResponseTextDeltaEvent):
            await msg.stream_token(event.data.delta)

    history.append({"role":"assistant","content":result.final_output})
    cl.user_session.set("history",history)





