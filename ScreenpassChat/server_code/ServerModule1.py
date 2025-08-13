import anvil.server
import json
import os
from datetime import datetime
import csv
import requests
import sys


# Global storage for conversation sessions
conversation_sessions = {}


def load_config():
    """Load all configuration files"""
    configs = {}
    
    try:
        # Load server config
        with open('roles/server_config.json', 'r') as f:
            configs['server'] = json.load(f)
        
        # Load company configs
        with open('roles/companyA.json', 'r') as f:
            configs['companyA'] = json.load(f)
        
        with open('roles/companyB.json', 'r') as f:
            configs['companyB'] = json.load(f)
        
        # Load questions
        with open('roles/questions.json', 'r') as f:
            configs['questions'] = json.load(f)
            
    except Exception as e:
        print(f"Error loading config files: {e}")
        # Return default config if files can't be loaded
        configs = {
            'server': {
                'agent_name': 'Screenpass',
                'agent_role': 'You are a trucker screenpass agent.',
                'initial_prompt': 'Hi, I\'m Screenpass. I\'m here to help you find the perfect trucking job with {}.',
                'api_key': '1234'
            },
            'companyA': {'name': 'Company A', 'yoe_required': 4, 'work_nights_per_week': 4},
            'companyB': {'name': 'Company B', 'yoe_required': 1, 'work_nights_per_week': 4}
        }
    
    return configs


def get_company_config(company_name):
    """Get company configuration based on company name"""
    configs = load_config()
    
    if company_name and company_name.lower() == 'companya':
        return configs['companyA']
    elif company_name and company_name.lower() == 'companyb':
        return configs['companyB']
    else:
        # Default to companyA if not found
        return configs.get('companyA', {'name': 'Company A', 'yoe_required': 4, 'work_nights_per_week': 4})


def call_llm(prompt, system_prompt=""):
    """Call the OpenAI API with proper error handling"""
    try:
        print(f"LLM: Making API call with prompt: {prompt[:100]}...")
        print(f"LLM: System prompt: {system_prompt[:200]}...")
        
        configs = load_config()
        api_key = configs['server'].get('api_key', '1234')
        
        # If using real API key (not the mock "1234")
        if api_key != "1234" and len(api_key) > 10:
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 500,
                'temperature': 0.7
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                message = result['choices'][0]['message']['content']
                print("LLM: API call succeeded")
                return message
            else:
                print(f"LLM: API call failed with status {response.status_code}: {response.text}")
                raise Exception(f"OpenAI API error: {response.status_code}")
                
        else:
            # Mock implementation for testing
            print("LLM: Using mock implementation (API key is '1234' or invalid)")
            mock_responses = [
                "Hi there! I'm excited to help you explore this trucking opportunity. Let me ask you a few questions to see if this might be a good fit.",
                "That's great! Can you tell me about your CDL and driving experience?",
                "Excellent! How many years of driving experience do you have?",
                "Perfect! Are you comfortable being on the road for several nights per week?",
                "Thank you for sharing that information. Based on what you've told me, I think you'd be a great fit for this position!",
                "I appreciate your interest. Let me tell you more about the benefits and compensation for this role.",
                "Do you have any questions about the company or the position?",
                "That's a great question! Let me provide you with those details."
            ]
            
            import random
            return random.choice(mock_responses)
            
    except Exception as e:
        print(f"LLM: Error in API call: {e}")
        print("LLM: Falling back to mock response")
        return "I'm sorry, I'm having some technical difficulties. Please try again in a moment."


@anvil.server.callable
def init_conversation(lead_source, company, session_id):
    """Initialize conversation with lead source and company information"""
    try:
        print(f"LLM: Initializing conversation for {company} from {lead_source}")
        
        # Load configurations
        company_config = get_company_config(company)
        configs = load_config()
        server_config = configs['server']
        
        # Populate system prompts with company-specific values
        yoe_required = company_config.get('yoe_required', 1)
        nights_per_week = company_config.get('work_nights_per_week', 4)
        company_name = company_config.get('name', company)
        
        # Format the initial prompt with company name
        initial_prompt = server_config['initial_prompt'].format(company_name)
        
        # Create comprehensive system prompt with agent goals and company facts
        agent_goals = server_config.get('agent_goals', [])
        goals_text = "\n".join([f"- {goal}" for goal in agent_goals])
        
        # Include company facts
        company_facts = f"""
        Company Information:
        - Name: {company_config.get('name', 'Unknown')}
        - Role Type: {company_config.get('role_type', 'N/A')}
        - Industry: {company_config.get('industry', 'N/A')}
        - Location: {company_config.get('location', 'N/A')}
        - Wage: ${company_config.get('wage', 'N/A')}/hour
        - Expected Miles per Day: {company_config.get('expected_miles_per_day', 'N/A')}
        - Work Hours: {company_config.get('work_start_time', 'N/A')} - {company_config.get('work_end_time', 'N/A')}
        - Health Insurance: {company_config.get('health_insurance', 'N/A')}
        - Dental Insurance: {company_config.get('dental_insurance', 'N/A')}
        - Vision Insurance: {company_config.get('vision_insurance', 'N/A')}
        - Retirement Plan: {company_config.get('retirement_plan', 'N/A')}
        """
        
        system_prompt = f"""
        {server_config['agent_role']}
        
        {company_facts}
        
        Requirements:
        - Years of Experience Required: {yoe_required}
        - Nights per week on road: {nights_per_week}
        - Valid, unexpired CDL required
        
        Agent Goals:
        {goals_text}
        
        Key Screening Questions (work these into the conversation naturally):
        1) We need a driver with a valid, unexpired CDL
        2) We need a driver with {yoe_required} years of experience, do not pass drivers who don't fit this requirement.
        3) This job requires being on the road for {nights_per_week} nights a week. Ask if that is okay?
        """
        
        # Store session data
        conversation_sessions[session_id] = {
            'history': [],
            'start_time': datetime.now(),
            'lead_source': lead_source,
            'company': company,
            'company_config': company_config
        }
        
        # Get initial response from LLM
        response_message = call_llm(initial_prompt, system_prompt)
        
        return {
            'success': True,
            'message': response_message,
            'company_config': company_config
        }
        
    except Exception as e:
        print(f"Error in init_conversation: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': "Welcome! I'm here to help you with your trucking career."
        }


@anvil.server.callable
def process_prompt(user_input, conversation_history, session_id):
    """Process user prompt and return LLM response"""
    try:
        print(f"LLM: Processing user input: {user_input[:50]}...")
        
        if session_id not in conversation_sessions:
            return {
                'success': False,
                'error': 'Session not found',
                'message': 'Please refresh the page and start a new conversation.'
            }
        
        session = conversation_sessions[session_id]
        
        # Update conversation history in session
        session['history'] = conversation_history
        
        # Build conversation context
        context = "\n".join(conversation_history[-10:])  # Last 10 messages for context
        
        # Get company info for context
        company_config = session['company_config']
        yoe_required = company_config.get('yoe_required', 1)
        nights_per_week = company_config.get('work_nights_per_week', 4)
        company_name = company_config.get('name', session['company'])
        
        # Create comprehensive system prompt with company facts and goals
        configs = load_config()
        server_config = configs['server']
        agent_goals = server_config.get('agent_goals', [])
        goals_text = "\n".join([f"- {goal}" for goal in agent_goals])
        
        # Include company facts
        company_facts = f"""
        Company Information:
        - Name: {company_config.get('name', 'Unknown')}
        - Role Type: {company_config.get('role_type', 'N/A')}
        - Industry: {company_config.get('industry', 'N/A')}
        - Location: {company_config.get('location', 'N/A')}
        - Wage: ${company_config.get('wage', 'N/A')}/hour
        - Expected Miles per Day: {company_config.get('expected_miles_per_day', 'N/A')}
        - Work Hours: {company_config.get('work_start_time', 'N/A')} - {company_config.get('work_end_time', 'N/A')}
        - Health Insurance: {company_config.get('health_insurance', 'N/A')}
        - Dental Insurance: {company_config.get('dental_insurance', 'N/A')}
        - Vision Insurance: {company_config.get('vision_insurance', 'N/A')}
        - Retirement Plan: {company_config.get('retirement_plan', 'N/A')}
        """
        
        system_prompt = f"""
        {server_config['agent_role']}
        
        {company_facts}
        
        Requirements:
        - Years of Experience Required: {yoe_required}
        - Nights per week on road: {nights_per_week}
        - Valid, unexpired CDL required
        
        Agent Goals:
        {goals_text}
        
        Key Screening Questions (work these into the conversation naturally):
        1) We need a driver with a valid, unexpired CDL
        2) We need a driver with {yoe_required} years of experience, do not pass drivers who don't fit this requirement.
        3) This job requires being on the road for {nights_per_week} nights a week. Ask if that is okay?
        
        Conversation so far:
        {context}
        
        Respond as the Screenpass agent. Be helpful, upbeat, and professional.
        """
        
        full_prompt = f"User just said: {user_input}\n\nPlease respond appropriately."
        
        # Get response from LLM
        response_message = call_llm(full_prompt, system_prompt)
        
        return {
            'success': True,
            'message': response_message
        }
        
    except Exception as e:
        print(f"Error in process_prompt: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': "I'm sorry, I encountered an error. Please try again."
        }


@anvil.server.callable
def summarize_conversation(conversation_history, start_time, end_time, lead_source, company, session_id):
    """Summarize conversation and perform all end-of-chat tasks"""
    try:
        print("LLM: Starting conversation summarization and analysis...")
        
        if session_id in conversation_sessions:
            session = conversation_sessions[session_id]
        else:
            # Create minimal session data if not found
            session = {
                'start_time': start_time,
                'lead_source': lead_source,
                'company': company
            }
        
        # Ensure results directories exist
        os.makedirs('results/audit', exist_ok=True)
        os.makedirs('results/summary', exist_ok=True)
        
        # 1. Save full conversation to audit folder
        timestamp_str = start_time.strftime("%Y%m%d_%H%M%S") + "_" + end_time.strftime("%Y%m%d_%H%M%S")
        audit_filename = f"results/audit/conversation_{timestamp_str}.txt"
        
        with open(audit_filename, 'w') as f:
            f.write(f"Conversation Log\n")
            f.write(f"Start Time: {start_time}\n")
            f.write(f"End Time: {end_time}\n")
            f.write(f"Lead Source: {lead_source}\n")
            f.write(f"Company: {company}\n")
            f.write(f"{'='*50}\n\n")
            
            for message in conversation_history:
                f.write(f"{message}\n")
        
        print(f"LLM: Saved conversation audit to {audit_filename}")
        
        # 2. Generate summary using LLM
        conversation_text = "\n".join(conversation_history)
        summary_prompt = f"""
        Please summarize the following conversation in 150 words or less:
        
        {conversation_text}
        
        Focus on key points discussed, driver qualifications, and outcome.
        """
        
        summary = call_llm(summary_prompt)
        
        # Save summary
        summary_filename = f"results/summary/summary_{timestamp_str}.txt"
        with open(summary_filename, 'w') as f:
            f.write(f"Conversation Summary\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write(f"Lead Source: {lead_source}\n")
            f.write(f"Company: {company}\n")
            f.write(f"{'='*50}\n\n")
            f.write(summary)
        
        print(f"LLM: Generated and saved summary to {summary_filename}")
        
        # 3. Perform sentiment analysis
        sentiment_prompt = f"""
        Analyze the sentiment and customer satisfaction of this conversation on a scale of 1-5 
        (1 = very dissatisfied, 5 = very satisfied):
        
        {conversation_text}
        
        Return only a number from 1 to 5.
        """
        
        sentiment_response = call_llm(sentiment_prompt)
        
        # Extract sentiment score
        try:
            sentiment_score = int(sentiment_response.strip())
            if sentiment_score < 1 or sentiment_score > 5:
                sentiment_score = 3  # Default to neutral
        except:
            sentiment_score = 3  # Default to neutral
        
        # Append to sentiment.csv
        with open('results/sentiment.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                company,
                lead_source,
                sentiment_score,
                f"conversation_{timestamp_str}"
            ])
        
        print(f"LLM: Added sentiment analysis (score: {sentiment_score}) to sentiment.csv")
        
        # 4. Determine if driver met qualifying criteria
        decision_prompt = f"""
        Based on this conversation, did the driver meet the qualifying criteria? 
        Consider: Valid CDL, required years of experience, willingness to be on road required nights.
        
        {conversation_text}
        
        Return 'QUALIFIED' or 'NOT_QUALIFIED' followed by a brief reason.
        """
        
        decision_response = call_llm(decision_prompt)
        
        # Parse decision
        if 'QUALIFIED' in decision_response.upper() and 'NOT_QUALIFIED' not in decision_response.upper():
            qualified = True
            reason = decision_response.replace('QUALIFIED', '').strip()
        else:
            qualified = False
            reason = decision_response.replace('NOT_QUALIFIED', '').strip()
        
        # Append to decisions.csv
        with open('results/decisions.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                company,
                lead_source,
                qualified,
                reason[:100]  # Limit reason length
            ])
        
        print(f"LLM: Added decision (qualified: {qualified}) to decisions.csv")
        
        # Clean up session from memory
        if session_id in conversation_sessions:
            del conversation_sessions[session_id]
        
        return {
            'success': True,
            'message': 'Conversation summarized and analyzed successfully',
            'summary': summary,
            'sentiment_score': sentiment_score,
            'qualified': qualified
        }
        
    except Exception as e:
        print(f"Error in summarize_conversation: {e}")
        return {
            'success': False,
            'error': str(e)
        }