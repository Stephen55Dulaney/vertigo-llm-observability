"""
Gmail Workflow Example using Vertex AI.
Demonstrates a complete workflow for email processing and analysis.
"""

import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime

# Import our modules
from agents.gmail_agent import GmailAgent
from search.vertex_search import VertexSearch
from gemini.gemini_client import GeminiClient
from workspace.agent_space import AgentSpace, SpaceAgent
from config.auth import auth


class EmailProcessingWorkflow:
    """
    Complete email processing workflow using Vertex AI components.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("email_workflow")
        
        # Initialize components
        self.gmail_agent = GmailAgent("Email Processor")
        self.search_client = VertexSearch()
        self.gemini_client = GeminiClient()
        
        # Create agent space for collaboration
        self.agent_space = AgentSpace("email-processing-space", "Email Processing Workspace")
        
        # Create specialized agents
        self.analysis_agent = EmailAnalysisAgent("analysis-agent", "Email Analysis Agent")
        self.summary_agent = EmailSummaryAgent("summary-agent", "Email Summary Agent")
        self.response_agent = EmailResponseAgent("response-agent", "Email Response Agent")
        
        # Join agents to the space
        asyncio.create_task(self.analysis_agent.join_space(self.agent_space))
        asyncio.create_task(self.summary_agent.join_space(self.agent_space))
        asyncio.create_task(self.response_agent.join_space(self.agent_space))
        
        self.logger.info("Email Processing Workflow initialized")
    
    async def process_inbox(self, max_emails: int = 10) -> Dict[str, Any]:
        """Process recent emails in the inbox."""
        try:
            self.logger.info(f"Starting inbox processing for {max_emails} emails")
            
            # Get recent emails
            emails = await self.gmail_agent.get_recent_emails(max_emails)
            
            if not emails:
                return {"status": "no_emails", "message": "No emails found"}
            
            results = []
            
            for email in emails:
                email_result = await self.process_single_email(email)
                results.append(email_result)
            
            # Create summary
            summary = await self.create_processing_summary(results)
            
            return {
                "status": "completed",
                "emails_processed": len(results),
                "results": results,
                "summary": summary
            }
            
        except Exception as e:
            self.logger.error(f"Error processing inbox: {e}")
            return {"status": "error", "error": str(e)}
    
    async def process_single_email(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single email through the workflow."""
        try:
            email_id = email['id']
            subject = email['subject']
            sender = email['sender']
            
            self.logger.info(f"Processing email: {subject} from {sender}")
            
            # Step 1: Analyze email content
            analysis = await self.gmail_agent.analyze_email_content(email_id)
            
            # Step 2: Create summary
            summary = await self.gemini_client.analyze_content(
                analysis.get('content', ''),
                analysis_type="summary"
            )
            
            # Step 3: Generate response if needed
            response = None
            if self._needs_response(analysis):
                response = await self.gmail_agent.draft_email_response(email_id)
            
            # Step 4: Store in search engine for future reference
            await self._store_email_for_search(email, analysis, summary)
            
            result = {
                "email_id": email_id,
                "subject": subject,
                "sender": sender,
                "analysis": analysis,
                "summary": summary,
                "response": response,
                "processed_at": datetime.now().isoformat()
            }
            
            self.logger.info(f"Email {email_id} processed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing email {email.get('id', 'unknown')}: {e}")
            return {
                "email_id": email.get('id', 'unknown'),
                "error": str(e),
                "processed_at": datetime.now().isoformat()
            }
    
    def _needs_response(self, analysis: Dict[str, Any]) -> bool:
        """Determine if an email needs a response."""
        content = analysis.get('analysis', '').lower()
        
        # Simple heuristics for response need
        response_indicators = [
            'question', 'request', 'please', 'need', 'help',
            'urgent', 'important', 'action required', 'respond'
        ]
        
        return any(indicator in content for indicator in response_indicators)
    
    async def _store_email_for_search(self, email: Dict[str, Any], analysis: Dict[str, Any], summary: Dict[str, Any]) -> None:
        """Store email information in search engine for future retrieval."""
        try:
            document = {
                "id": email['id'],
                "title": email['subject'],
                "content": f"{email.get('snippet', '')}\n\n{analysis.get('content', '')}\n\n{summary.get('analysis', '')}",
                "metadata": {
                    "sender": email['sender'],
                    "date": email['date'],
                    "thread_id": email.get('threadId', ''),
                    "analysis_type": analysis.get('analysis', ''),
                    "summary": summary.get('analysis', '')
                }
            }
            
            # Add to search engine (simulated)
            await self.search_client.add_documents("email-engine", [document])
            
        except Exception as e:
            self.logger.error(f"Error storing email for search: {e}")
    
    async def create_processing_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a summary of email processing results."""
        try:
            successful_emails = [r for r in results if 'error' not in r]
            failed_emails = [r for r in results if 'error' in r]
            
            # Generate summary using Gemini
            summary_prompt = f"""
            Create a summary of email processing results:
            
            Total emails processed: {len(results)}
            Successful: {len(successful_emails)}
            Failed: {len(failed_emails)}
            
            Email subjects: {[r.get('subject', 'No subject') for r in successful_emails]}
            
            Please provide:
            1. Overall processing status
            2. Key themes or topics from emails
            3. Any urgent items that need attention
            4. Recommendations for follow-up
            """
            
            summary_response = await self.gemini_client.generate_text(summary_prompt)
            
            return {
                "total_processed": len(results),
                "successful": len(successful_emails),
                "failed": len(failed_emails),
                "summary_text": summary_response,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error creating processing summary: {e}")
            return {"error": str(e)}
    
    async def search_emails(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search through processed emails."""
        try:
            # Use RAG to search and generate responses
            response = await self.search_client.rag_query(query, "email-engine")
            
            # Also search Gmail directly
            gmail_results = await self.gmail_agent.search_emails(query, max_results)
            
            return {
                "rag_response": response,
                "gmail_results": gmail_results,
                "query": query
            }
            
        except Exception as e:
            self.logger.error(f"Error searching emails: {e}")
            return {"error": str(e)}


class EmailAnalysisAgent(SpaceAgent):
    """Specialized agent for email analysis."""
    
    async def perform_task(self, task: str, context: Dict[str, Any] = None) -> Any:
        """Perform email analysis tasks."""
        try:
            if "analyze" in task.lower():
                # Use Gemini for analysis
                from gemini.gemini_client import GeminiClient
                client = GeminiClient()
                
                content = context.get('content', '')
                analysis = await client.analyze_content(content, "general")
                
                return {
                    "task": task,
                    "analysis": analysis,
                    "agent": self.agent_id
                }
            
            return {"status": "completed", "task": task, "agent": self.agent_id}
            
        except Exception as e:
            return {"error": str(e), "task": task, "agent": self.agent_id}


class EmailSummaryAgent(SpaceAgent):
    """Specialized agent for email summarization."""
    
    async def perform_task(self, task: str, context: Dict[str, Any] = None) -> Any:
        """Perform email summarization tasks."""
        try:
            if "summarize" in task.lower():
                from gemini.gemini_client import GeminiClient
                client = GeminiClient()
                
                content = context.get('content', '')
                summary = await client.analyze_content(content, "summary")
                
                return {
                    "task": task,
                    "summary": summary,
                    "agent": self.agent_id
                }
            
            return {"status": "completed", "task": task, "agent": self.agent_id}
            
        except Exception as e:
            return {"error": str(e), "task": task, "agent": self.agent_id}


class EmailResponseAgent(SpaceAgent):
    """Specialized agent for email response generation."""
    
    async def perform_task(self, task: str, context: Dict[str, Any] = None) -> Any:
        """Perform email response generation tasks."""
        try:
            if "respond" in task.lower():
                from gemini.gemini_client import GeminiClient
                client = GeminiClient()
                
                original_content = context.get('content', '')
                response = await client.creative_writing(
                    f"Write a professional response to this email: {original_content}",
                    style="professional"
                )
                
                return {
                    "task": task,
                    "response": response,
                    "agent": self.agent_id
                }
            
            return {"status": "completed", "task": task, "agent": self.agent_id}
            
        except Exception as e:
            return {"error": str(e), "task": task, "agent": self.agent_id}


# Example usage
async def main():
    """Example usage of the Email Processing Workflow."""
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create workflow
    workflow = EmailProcessingWorkflow()
    
    # Process recent emails
    print("Processing recent emails...")
    result = await workflow.process_inbox(max_emails=5)
    
    print(f"Processing result: {result}")
    
    # Search for specific emails
    print("\nSearching for emails about 'meeting'...")
    search_result = await workflow.search_emails("meeting")
    print(f"Search result: {search_result}")


if __name__ == "__main__":
    asyncio.run(main()) 