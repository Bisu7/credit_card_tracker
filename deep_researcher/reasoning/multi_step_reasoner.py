"""Multi-step reasoning for complex query decomposition and execution."""

import uuid
import time
from typing import List, Dict, Any, Optional, Set
import logging
from dataclasses import dataclass
from enum import Enum

from ..models import ProcessedQuery, ReasoningStep, QueryType
from ..interfaces import MultiStepReasonerInterface
from ..exceptions import ReasoningError
from ..config import config

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    """Status of a reasoning step."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ReasoningContext:
    """Context maintained during reasoning execution."""
    original_query: ProcessedQuery
    steps: List[ReasoningStep]
    step_results: Dict[str, Any]
    global_context: Dict[str, Any]
    execution_order: List[str]
    failed_steps: List[str]
    start_time: float
    
    def get_step_by_id(self, step_id: str) -> Optional[ReasoningStep]:
        """Get a step by its ID."""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None
    
    def is_step_completed(self, step_id: str) -> bool:
        """Check if a step is completed."""
        return step_id in self.step_results
    
    def get_completed_steps(self) -> List[str]:
        """Get list of completed step IDs."""
        return list(self.step_results.keys())


class MultiStepReasoner(MultiStepReasonerInterface):
    """Handles multi-step reasoning for complex queries."""
    
    def __init__(self, max_steps: Optional[int] = None):
        """
        Initialize multi-step reasoner.
        
        Args:
            max_steps: Maximum number of reasoning steps allowed
        """
        self.max_steps = max_steps or config.max_reasoning_steps
        
        # Reasoning templates for different query types
        self.reasoning_templates = {
            QueryType.COMPARATIVE: self._create_comparative_steps,
            QueryType.ANALYTICAL: self._create_analytical_steps,
            QueryType.MULTI_PART: self._create_multi_part_steps,
            QueryType.COMPLEX: self._create_complex_steps
        }
    
    def create_reasoning_plan(self, query: ProcessedQuery) -> List[ReasoningStep]:
        """
        Create a plan for multi-step reasoning.
        
        Args:
            query: Processed query to create plan for
            
        Returns:
            List of reasoning steps
        """
        try:
            logger.info(f"Creating reasoning plan for {query.query_type.value} query")
            
            # Get appropriate template
            template_func = self.reasoning_templates.get(
                query.query_type, 
                self._create_default_steps
            )
            
            # Generate steps using template
            steps = template_func(query)
            
            # Validate and optimize plan
            steps = self._validate_and_optimize_plan(steps, query)
            
            # Limit number of steps
            if len(steps) > self.max_steps:
                logger.warning(f"Plan has {len(steps)} steps, limiting to {self.max_steps}")
                steps = steps[:self.max_steps]
            
            logger.info(f"Created reasoning plan with {len(steps)} steps")
            return steps
            
        except Exception as e:
            logger.error(f"Failed to create reasoning plan: {e}")
            raise ReasoningError(f"Failed to create reasoning plan: {e}")
    
    def execute_reasoning_step(self, step: ReasoningStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single reasoning step.
        
        Args:
            step: Reasoning step to execute
            context: Current reasoning context
            
        Returns:
            Step execution results
        """
        try:
            logger.debug(f"Executing reasoning step: {step.step_id}")
            start_time = time.time()
            
            # Check dependencies
            missing_deps = self._check_dependencies(step, context)
            if missing_deps:
                raise ReasoningError(f"Missing dependencies: {missing_deps}")
            
            # Execute step based on its type/description
            result = self._execute_step_logic(step, context)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Update step with results
            step.results = result
            step.execution_time = execution_time
            
            logger.debug(f"Step {step.step_id} completed in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Step execution failed for {step.step_id}: {e}")
            step.results = {"error": str(e), "status": "failed"}
            raise ReasoningError(f"Step execution failed: {e}")
    
    def execute_full_reasoning(self, query: ProcessedQuery) -> ReasoningContext:
        """
        Execute complete multi-step reasoning for a query.
        
        Args:
            query: Processed query to reason about
            
        Returns:
            Complete reasoning context with results
        """
        try:
            logger.info(f"Starting full reasoning for query: {query.original_query}")
            
            # Create reasoning plan
            steps = self.create_reasoning_plan(query)
            
            # Initialize context
            context = ReasoningContext(
                original_query=query,
                steps=steps,
                step_results={},
                global_context={
                    "query_keywords": query.keywords,
                    "query_type": query.query_type.value,
                    "complexity_score": query.complexity_score
                },
                execution_order=[],
                failed_steps=[],
                start_time=time.time()
            )
            
            # Execute steps in dependency order
            execution_order = self._determine_execution_order(steps)
            
            for step_id in execution_order:
                step = context.get_step_by_id(step_id)
                if not step:
                    continue
                
                try:
                    # Execute step
                    result = self.execute_reasoning_step(step, context.step_results)
                    
                    # Store results
                    context.step_results[step_id] = result
                    context.execution_order.append(step_id)
                    
                    # Update global context with important findings
                    self._update_global_context(context, step, result)
                    
                except ReasoningError as e:
                    logger.warning(f"Step {step_id} failed: {e}")
                    context.failed_steps.append(step_id)
                    
                    # Decide whether to continue or abort
                    if self._should_abort_on_failure(step, context):
                        logger.error(f"Aborting reasoning due to critical step failure: {step_id}")
                        break
            
            total_time = time.time() - context.start_time
            logger.info(f"Reasoning completed in {total_time:.2f}s. "
                       f"Completed: {len(context.step_results)}, Failed: {len(context.failed_steps)}")
            
            return context
            
        except Exception as e:
            logger.error(f"Full reasoning execution failed: {e}")
            raise ReasoningError(f"Full reasoning execution failed: {e}")
    
    def _create_comparative_steps(self, query: ProcessedQuery) -> List[ReasoningStep]:
        """Create steps for comparative queries."""
        steps = []
        
        # Extract entities to compare
        entities = query.keywords[:2] if len(query.keywords) >= 2 else ["entity1", "entity2"]
        
        # Step 1: Research first entity
        steps.append(ReasoningStep(
            step_id=str(uuid.uuid4()),
            description=f"Research and gather information about {entities[0]}",
            query=f"What is {entities[0]}? Provide comprehensive information.",
            confidence=0.9
        ))
        
        # Step 2: Research second entity
        steps.append(ReasoningStep(
            step_id=str(uuid.uuid4()),
            description=f"Research and gather information about {entities[1]}",
            query=f"What is {entities[1]}? Provide comprehensive information.",
            confidence=0.9
        ))
        
        # Step 3: Identify comparison dimensions
        steps.append(ReasoningStep(
            step_id=str(uuid.uuid4()),
            description="Identify key dimensions for comparison",
            query=f"What are the main aspects to compare between {entities[0]} and {entities[1]}?",
            dependencies=[steps[0].step_id, steps[1].step_id],
            confidence=0.8
        ))
        
        # Step 4: Perform detailed comparison
        steps.append(ReasoningStep(
            step_id=str(uuid.uuid4()),
            description="Perform detailed comparison analysis",
            query=f"Compare {entities[0]} and {entities[1]} across identified dimensions",
            dependencies=[steps[2].step_id],
            confidence=0.85
        ))
        
        return steps
    
    def _create_analytical_steps(self, query: ProcessedQuery) -> List[ReasoningStep]:
        """Create steps for analytical queries."""
        steps = []
        
        # Step 1: Define the problem/topic
        steps.append(ReasoningStep(
            step_id=str(uuid.uuid4()),
            description="Define and understand the analytical problem",
            query=f"What is the core problem or topic in: {query.original_query}?",
            confidence=0.9
        ))
        
        # Step 2: Identify key factors
        steps.append(ReasoningStep(
            step_id=str(uuid.uuid4()),
            description="Identify key factors and variables",
            query="What are the main factors, variables, or components involved?",
            dependencies=[steps[0].step_id],
            confidence=0.8
        ))
        
        # Step 3: Gather evidence
        steps.append(ReasoningStep(
            step_id=str(uuid.uuid4()),
            description="Gather evidence and data",
            query="What evidence, data, or research supports analysis of these factors?",
            dependencies=[steps[1].step_id],
            confidence=0.85
        ))
        
        # Step 4: Analyze relationships
        steps.append(ReasoningStep(
            step_id=str(uuid.uuid4()),
            description="Analyze relationships and patterns",
            query="How do the identified factors relate to each other? What patterns emerge?",
            dependencies=[steps[2].step_id],
            confidence=0.8
        ))
        
        # Step 5: Draw conclusions
        steps.append(ReasoningStep(
            step_id=str(uuid.uuid4()),
            description="Draw analytical conclusions",
            query="Based on the analysis, what conclusions can be drawn?",
            dependencies=[steps[3].step_id],
            confidence=0.75
        ))
        
        return steps
    
    def _create_multi_part_steps(self, query: ProcessedQuery) -> List[ReasoningStep]:
        """Create steps for multi-part queries."""
        steps = []
        
        # Use sub-queries if available
        if query.sub_queries:
            for i, sub_query in enumerate(query.sub_queries):
                steps.append(ReasoningStep(
                    step_id=str(uuid.uuid4()),
                    description=f"Address sub-question {i+1}",
                    query=sub_query,
                    confidence=0.85
                ))
        else:
            # Break down based on keywords
            for i, keyword in enumerate(query.keywords[:3]):
                steps.append(ReasoningStep(
                    step_id=str(uuid.uuid4()),
                    description=f"Research aspect: {keyword}",
                    query=f"Provide information about {keyword} in the context of: {query.original_query}",
                    confidence=0.8
                ))
        
        # Add synthesis step
        if len(steps) > 1:
            synthesis_deps = [step.step_id for step in steps]
            steps.append(ReasoningStep(
                step_id=str(uuid.uuid4()),
                description="Synthesize findings from all parts",
                query="How do all the researched aspects relate to answer the original question?",
                dependencies=synthesis_deps,
                confidence=0.75
            ))
        
        return steps
    
    def _create_complex_steps(self, query: ProcessedQuery) -> List[ReasoningStep]:
        """Create steps for complex queries."""
        steps = []
        
        # Step 1: Break down complexity
        steps.append(ReasoningStep(
            step_id=str(uuid.uuid4()),
            description="Break down the complex query into components",
            query=f"What are the main components or aspects of: {query.original_query}?",
            confidence=0.8
        ))
        
        # Step 2: Research each component
        for i, keyword in enumerate(query.keywords[:3]):
            steps.append(ReasoningStep(
                step_id=str(uuid.uuid4()),
                description=f"Research component: {keyword}",
                query=f"Provide detailed information about {keyword}",
                dependencies=[steps[0].step_id],
                confidence=0.85
            ))
        
        # Step 3: Analyze interactions
        if len(query.keywords) > 1:
            component_deps = [step.step_id for step in steps[1:]]
            steps.append(ReasoningStep(
                step_id=str(uuid.uuid4()),
                description="Analyze interactions between components",
                query="How do these components interact or influence each other?",
                dependencies=component_deps,
                confidence=0.75
            ))
        
        return steps
    
    def _create_default_steps(self, query: ProcessedQuery) -> List[ReasoningStep]:
        """Create default steps for simple queries."""
        steps = []
        
        # Single comprehensive research step
        steps.append(ReasoningStep(
            step_id=str(uuid.uuid4()),
            description="Research the query topic comprehensively",
            query=query.original_query,
            confidence=0.9
        ))
        
        return steps
    
    def _validate_and_optimize_plan(self, steps: List[ReasoningStep], query: ProcessedQuery) -> List[ReasoningStep]:
        """Validate and optimize the reasoning plan."""
        # Remove duplicate steps
        seen_queries = set()
        unique_steps = []
        
        for step in steps:
            if step.query.lower() not in seen_queries:
                seen_queries.add(step.query.lower())
                unique_steps.append(step)
        
        # Validate dependencies
        step_ids = {step.step_id for step in unique_steps}
        for step in unique_steps:
            # Remove invalid dependencies
            step.dependencies = [dep for dep in step.dependencies if dep in step_ids]
        
        # Check for circular dependencies
        if self._has_circular_dependencies(unique_steps):
            logger.warning("Circular dependencies detected, removing some dependencies")
            unique_steps = self._resolve_circular_dependencies(unique_steps)
        
        return unique_steps
    
    def _has_circular_dependencies(self, steps: List[ReasoningStep]) -> bool:
        """Check if there are circular dependencies in the steps."""
        # Simple cycle detection using DFS
        step_map = {step.step_id: step for step in steps}
        visited = set()
        rec_stack = set()
        
        def has_cycle(step_id: str) -> bool:
            if step_id in rec_stack:
                return True
            if step_id in visited:
                return False
            
            visited.add(step_id)
            rec_stack.add(step_id)
            
            step = step_map.get(step_id)
            if step:
                for dep in step.dependencies:
                    if has_cycle(dep):
                        return True
            
            rec_stack.remove(step_id)
            return False
        
        for step in steps:
            if step.step_id not in visited:
                if has_cycle(step.step_id):
                    return True
        
        return False
    
    def _resolve_circular_dependencies(self, steps: List[ReasoningStep]) -> List[ReasoningStep]:
        """Resolve circular dependencies by removing some dependencies."""
        # Simple resolution: remove dependencies that create cycles
        for step in steps:
            step.dependencies = []  # Reset all dependencies
        
        return steps
    
    def _determine_execution_order(self, steps: List[ReasoningStep]) -> List[str]:
        """Determine the order to execute steps based on dependencies."""
        # Topological sort
        step_map = {step.step_id: step for step in steps}
        in_degree = {step.step_id: 0 for step in steps}
        
        # Calculate in-degrees
        for step in steps:
            for dep in step.dependencies:
                if dep in in_degree:
                    in_degree[step.step_id] += 1
        
        # Find steps with no dependencies
        queue = [step_id for step_id, degree in in_degree.items() if degree == 0]
        execution_order = []
        
        while queue:
            current = queue.pop(0)
            execution_order.append(current)
            
            # Update in-degrees of dependent steps
            current_step = step_map.get(current)
            if current_step:
                for step in steps:
                    if current in step.dependencies:
                        in_degree[step.step_id] -= 1
                        if in_degree[step.step_id] == 0:
                            queue.append(step.step_id)
        
        return execution_order
    
    def _check_dependencies(self, step: ReasoningStep, context: Dict[str, Any]) -> List[str]:
        """Check if step dependencies are satisfied."""
        missing = []
        for dep in step.dependencies:
            if dep not in context:
                missing.append(dep)
        return missing
    
    def _execute_step_logic(self, step: ReasoningStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the actual logic for a reasoning step."""
        # This is a simplified implementation
        # In a full system, this would integrate with document retrieval and synthesis
        
        result = {
            "step_id": step.step_id,
            "query": step.query,
            "status": "completed",
            "findings": [],
            "confidence": step.confidence,
            "context_used": list(context.keys())
        }
        
        # Simulate processing based on step description
        if "research" in step.description.lower():
            result["findings"] = [f"Research finding for: {step.query}"]
            result["source_count"] = 3
        elif "compare" in step.description.lower():
            result["findings"] = ["Comparison analysis completed"]
            result["comparison_dimensions"] = ["feature1", "feature2", "feature3"]
        elif "analyze" in step.description.lower():
            result["findings"] = ["Analysis completed"]
            result["key_factors"] = ["factor1", "factor2"]
        
        return result
    
    def _update_global_context(self, context: ReasoningContext, step: ReasoningStep, result: Dict[str, Any]) -> None:
        """Update global context with step results."""
        # Extract important information from step results
        if "findings" in result:
            if "all_findings" not in context.global_context:
                context.global_context["all_findings"] = []
            context.global_context["all_findings"].extend(result["findings"])
        
        if "key_factors" in result:
            if "factors" not in context.global_context:
                context.global_context["factors"] = []
            context.global_context["factors"].extend(result["key_factors"])
    
    def _should_abort_on_failure(self, step: ReasoningStep, context: ReasoningContext) -> bool:
        """Determine if reasoning should abort on step failure."""
        # Don't abort if we have some successful steps
        if len(context.step_results) > 0:
            return False
        
        # Abort if too many steps have failed
        if len(context.failed_steps) > len(context.steps) // 2:
            return True
        
        return False
    
    def get_reasoning_summary(self, context: ReasoningContext) -> Dict[str, Any]:
        """Generate a summary of the reasoning process."""
        total_time = time.time() - context.start_time
        
        return {
            "original_query": context.original_query.original_query,
            "query_type": context.original_query.query_type.value,
            "total_steps": len(context.steps),
            "completed_steps": len(context.step_results),
            "failed_steps": len(context.failed_steps),
            "execution_time": total_time,
            "success_rate": len(context.step_results) / len(context.steps) if context.steps else 0,
            "execution_order": context.execution_order,
            "global_findings": context.global_context.get("all_findings", []),
            "key_factors": context.global_context.get("factors", [])
        }