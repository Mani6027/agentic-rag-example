"""Plan-and-execute agent executor for data analysis."""

from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from src.agent.tools import create_tools
from src.agent.prompts import AGENT_SYSTEM_PROMPT, get_context_prompt
from src.data.storage import data_store
from src.rag.vector_store import vector_store_manager
from src.config.settings import settings
from src.utils.logger import logger


class DataAnalysisAgent:
    """Agent for analyzing Excel data using ReAct pattern with RAG context."""

    def __init__(self):
        """Initialize the agent executor."""
        self.llm = ChatGoogleGenerativeAI(
            model=settings.model_name,
            temperature=settings.temperature,
            google_api_key=settings.google_api_key
        )
        logger.info(f"Initialized LLM: {settings.model_name}")

    def _get_rag_context(
        self,
        dataset_id: str,
        query: str,
        k: int = 5
    ) -> str:
        """
        Retrieve relevant context from RAG.

        Args:
            dataset_id: Dataset identifier
            query: User query
            k: Number of documents to retrieve

        Returns:
            Context string from RAG
        """
        try:
            docs = vector_store_manager.query_metadata(
                dataset_id,
                query,
                k=k
            )

            if not docs:
                return "No relevant metadata found."

            context_parts = []
            for i, doc in enumerate(docs, 1):
                context_parts.append(f"[Context {i}]\n{doc.page_content}")

            return "\n\n".join(context_parts)

        except Exception as e:
            logger.error(f"Error retrieving RAG context: {str(e)}")
            return f"Error retrieving context: {str(e)}"

    def _get_sample_data(
        self,
        dataset_id: str,
        sheet_name: str,
        n: int = 3
    ) -> str:
        """
        Get sample data for context.

        Args:
            dataset_id: Dataset identifier
            sheet_name: Sheet name
            n: Number of sample rows

        Returns:
            Sample data as formatted string
        """
        try:
            df = data_store.get_dataframe(dataset_id, sheet_name)
            sample = df.head(n)
            return sample.to_string()
        except Exception as e:
            logger.error(f"Error getting sample data: {str(e)}")
            return "Error retrieving sample data"

    def query(
        self,
        dataset_id: str,
        sheet_name: str,
        user_query: str
    ) -> Dict[str, Any]:
        """
        Execute a query against the dataset using ReAct agent.

        Args:
            dataset_id: Dataset identifier
            sheet_name: Sheet name
            user_query: User's natural language query

        Returns:
            Dictionary with query results and reasoning
        """
        try:
            logger.info(
                f"Processing query for dataset {dataset_id}, "
                f"sheet {sheet_name}: '{user_query}'"
            )

            # Get DataFrame info
            df = data_store.get_dataframe(dataset_id, sheet_name)
            columns = list(df.columns)

            # Get RAG context
            rag_context = self._get_rag_context(dataset_id, user_query, k=5)

            # Get sample data
            sample_data = self._get_sample_data(dataset_id, sheet_name, n=3)

            # Create tools with access to this dataset
            tools = create_tools(dataset_id, sheet_name)

            # Build context prompt
            context = get_context_prompt(columns, sample_data, rag_context)

            # Create ReAct agent prompt
            react_prompt = PromptTemplate.from_template(
                """You are an AI data analyst. Answer the user's question about the Excel dataset accurately.

{system_prompt}

{context}

TOOLS:
------
You have access to the following tools:

{tools}

Tool Names: {tool_names}

RESPONSE FORMAT:
---------------
Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Important:
- Always use exact column names from the dataset
- Start by understanding the schema if needed (use get_column_info or query_schema)
- For calculations, use the appropriate tools
- Be precise with numbers
- Explain your reasoning in the Final Answer

Begin!

Question: {input}
Thought: {agent_scratchpad}"""
            )

            # Create ReAct agent
            agent = create_react_agent(
                llm=self.llm,
                tools=tools,
                prompt=react_prompt
            )

            # Create agent executor
            agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                max_iterations=settings.max_iterations,
                handle_parsing_errors=True,
                return_intermediate_steps=True
            )

            # Execute query
            result = agent_executor.invoke({
                "input": user_query,
                "system_prompt": AGENT_SYSTEM_PROMPT,
                "context": context
            })

            # Extract execution steps
            execution_steps = []
            if "intermediate_steps" in result:
                for i, (action, observation) in enumerate(result["intermediate_steps"], 1):
                    execution_steps.append({
                        "step": i,
                        "action": action.tool,
                        "action_input": action.tool_input,
                        "observation": str(observation)[:500]  # Limit observation length
                    })

            response = {
                "query": user_query,
                "answer": result.get("output", "No answer generated"),
                "execution_steps": execution_steps,
                "rag_context_used": rag_context[:500],  # Include snippet of RAG context
                "success": True
            }

            logger.info(f"Query completed successfully")
            return response

        except Exception as e:
            logger.error(f"Error executing query: {str(e)}", exc_info=True)
            return {
                "query": user_query,
                "answer": f"Error processing query: {str(e)}",
                "execution_steps": [],
                "success": False,
                "error": str(e)
            }


# Global agent instance
data_analysis_agent = DataAnalysisAgent()
