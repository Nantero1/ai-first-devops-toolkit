"""
Pydantic schema models for structured output examples.

This module demonstrates how to create comprehensive schemas for LLM structured output
using Semantic Kernel's KernelBaseModel for guaranteed JSON format compliance.
"""

from typing import List, Optional
from pydantic import Field
from semantic_kernel.kernel_pydantic import KernelBaseModel


class CodeIssue(KernelBaseModel):
    """Represents a specific issue found in the code."""

    severity: str = Field(
        description="Severity level of the issue",
        examples=["critical", "major", "minor", "suggestion"],
    )
    category: str = Field(
        description="Category of the issue",
        examples=["security", "performance", "maintainability", "style", "logic"],
    )
    line_number: Optional[int] = Field(
        description="Line number where the issue occurs (if applicable)",
        examples=[1, 5, 12],
        ge=1,
    )
    issue_description: str = Field(
        description="Clear description of what the issue is",
        examples=[
            "Missing input validation for negative prices",
            "Function lacks proper error handling",
            "Variable naming could be more descriptive",
        ],
    )
    suggested_fix: str = Field(
        description="Specific suggestion on how to fix the issue",
        examples=[
            "Add validation to ensure price is greater than 0",
            "Wrap calculations in try-catch block",
            "Rename 'discount_percent' to 'discount_percentage'",
        ],
    )


class QualityRating(KernelBaseModel):
    """Represents a quality rating for a specific aspect of the code."""

    aspect: str = Field(
        description="The specific aspect being rated",
        examples=[
            "readability",
            "maintainability",
            "performance",
            "security",
            "testability",
        ],
    )
    score: int = Field(
        description="Rating score from 1 to 10", examples=[7, 8, 9], ge=1, le=10
    )
    justification: str = Field(
        description="Explanation for the given score",
        examples=[
            "Code is mostly readable but variable names could be improved",
            "Good separation of concerns and follows single responsibility principle",
            "Function is efficient but could benefit from input validation",
        ],
    )


class CodeReviewAnalysis(KernelBaseModel):
    """Complete code review analysis with structured feedback."""

    overall_assessment: str = Field(
        description="High-level summary of the code quality",
        examples=[
            "Good foundation but needs input validation and error handling",
            "Well-structured code with minor style improvements needed",
            "Solid implementation with excellent maintainability",
        ],
    )

    issues: List[CodeIssue] = Field(
        description="List of specific issues found in the code", min_items=0
    )

    quality_ratings: List[QualityRating] = Field(
        description="Ratings for different quality aspects", min_items=1
    )

    positive_aspects: List[str] = Field(
        description="Things that are done well in the code",
        examples=[
            "Clear function name that describes its purpose",
            "Good handling of edge cases",
            "Logical flow and structure",
        ],
        min_items=0,
    )

    improvement_suggestions: List[str] = Field(
        description="General suggestions for improvement",
        examples=[
            "Add comprehensive input validation",
            "Include unit tests to verify functionality",
            "Consider adding docstring documentation",
        ],
        min_items=0,
    )

    complexity_score: int = Field(
        description="Code complexity rating from 1 (simple) to 10 (very complex)",
        examples=[3, 5, 7],
        ge=1,
        le=10,
    )

    # Example configuration to show LLM how fields work together
    class Config:
        json_schema_extra = {
            "example": {
                "overall_assessment": "Good foundation but needs input validation and error handling",
                "issues": [
                    {
                        "severity": "major",
                        "category": "security",
                        "line_number": 1,
                        "issue_description": "Missing input validation for price parameter",
                        "suggested_fix": "Add validation to ensure price is a positive number",
                    },
                    {
                        "severity": "minor",
                        "category": "style",
                        "line_number": None,
                        "issue_description": "Function lacks docstring documentation",
                        "suggested_fix": "Add docstring explaining parameters, return value, and behavior",
                    },
                ],
                "quality_ratings": [
                    {
                        "aspect": "readability",
                        "score": 8,
                        "justification": "Code is clear and easy to follow with logical structure",
                    },
                    {
                        "aspect": "security",
                        "score": 4,
                        "justification": "Missing input validation makes it vulnerable to invalid inputs",
                    },
                ],
                "positive_aspects": [
                    "Clear function name that describes its purpose",
                    "Handles edge cases for discount percentage bounds",
                    "Simple and straightforward logic",
                ],
                "improvement_suggestions": [
                    "Add comprehensive input validation for both parameters",
                    "Include proper error handling with meaningful error messages",
                    "Add unit tests to verify edge cases",
                ],
                "complexity_score": 3,
            }
        }


# Additional schema examples for different use cases


class SentimentAnalysis(KernelBaseModel):
    """Schema for sentiment analysis tasks."""

    overall_sentiment: str = Field(
        description="Overall sentiment of the text",
        examples=["positive", "negative", "neutral", "mixed"],
    )
    confidence_score: float = Field(
        description="Confidence level for the sentiment analysis",
        examples=[0.95, 0.87, 0.76],
        ge=0.0,
        le=1.0,
    )
    key_phrases: List[str] = Field(
        description="Important phrases that influenced the sentiment",
        examples=["excellent quality", "terrible experience", "works as expected"],
    )
    emotion_breakdown: dict = Field(
        description="Breakdown of emotions detected",
        examples=[
            {"joy": 0.8, "anger": 0.1, "sadness": 0.05, "fear": 0.05},
            {"satisfaction": 0.7, "disappointment": 0.2, "neutral": 0.1},
        ],
    )


class ProductExtraction(KernelBaseModel):
    """Schema for extracting product information from text."""

    product_name: str = Field(
        description="Name of the product",
        examples=["iPhone 15 Pro", "MacBook Air M2", "AirPods Pro"],
    )
    brand: str = Field(
        description="Brand or manufacturer name", examples=["Apple", "Samsung", "Sony"]
    )
    price: Optional[float] = Field(
        description="Price of the product if mentioned",
        examples=[999.99, 1299.00, 199.99],
        ge=0,
    )
    features: List[str] = Field(
        description="Key features mentioned",
        examples=["48MP camera", "All-day battery life", "5G connectivity"],
    )
    availability: Optional[str] = Field(
        description="Availability status if mentioned",
        examples=["in stock", "out of stock", "pre-order", "coming soon"],
    )
