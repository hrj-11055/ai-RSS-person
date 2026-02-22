"""
Cost tracking utility for AI-RSS-PERSON project.

Extracted from daily_report_PRO_cloud.py to provide consistent
cost tracking across all modules and scripts.
"""

from typing import Optional


class CostTracker:
    """
    Track API usage and calculate costs.

    This class tracks input and output tokens from AI API calls
    and calculates the associated costs based on configured pricing.

    Default pricing (DeepSeek):
    - Input tokens: ¥2 per million tokens
    - Output tokens: ¥3 per million tokens

    Example:
        >>> tracker = CostTracker(price_input=2.0, price_output=3.0)
        >>> tracker.add(usage_object)
        >>> print(tracker.report())
        📊 本次消耗: 输入 50000 | 输出 10000 | 费用: ¥0.13000
    """

    def __init__(self, price_input: float = 2.0, price_output: float = 3.0):
        """
        Initialize the cost tracker.

        Args:
            price_input: Price per million input tokens (default: ¥2.0)
            price_output: Price per million output tokens (default: ¥3.0)
        """
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.price_input = price_input
        self.price_output = price_output

    def add(self, usage) -> None:
        """
        Add token usage from an API response.

        Args:
            usage: Usage object with prompt_tokens and completion_tokens attributes
                  (typically from OpenAI API response)

        Example:
            >>> response = client.chat.completions.create(...)
            >>> tracker.add(response.usage)
        """
        if usage:
            self.total_input_tokens += usage.prompt_tokens
            self.total_output_tokens += usage.completion_tokens

    def add_tokens(self, input_tokens: int, output_tokens: int) -> None:
        """
        Add tokens directly without a usage object.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Example:
            >>> tracker.add_tokens(1000, 500)
        """
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

    def get_cost(self) -> float:
        """
        Calculate the total cost.

        Returns:
            Total cost in CNY

        Example:
            >>> cost = tracker.get_cost()
            >>> print(f"Total cost: ¥{cost:.2f}")
        """
        cost = (
            self.total_input_tokens / 1_000_000 * self.price_input
            + self.total_output_tokens / 1_000_000 * self.price_output
        )
        return cost

    def report(self, emoji: str = "📊") -> str:
        """
        Generate a formatted cost report.

        Args:
            emoji: Emoji to prefix the report (default: 📊)

        Returns:
            Formatted report string

        Example:
            >>> print(tracker.report())
            📊 本次消耗: 输入 50000 | 输出 10000 | 费用: ¥0.13000
        """
        cost = self.get_cost()
        return (
            f"{emoji} 本次消耗: 输入 {self.total_input_tokens} | "
            f"输出 {self.total_output_tokens} | 费用: ¥{cost:.5f}"
        )

    def reset(self) -> None:
        """
        Reset all counters to zero.

        Example:
            >>> tracker.reset()
        """
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def get_totals(self) -> tuple[int, int]:
        """
        Get total tokens tracked.

        Returns:
            Tuple of (input_tokens, output_tokens)

        Example:
            >>> input_tokens, output_tokens = tracker.get_totals()
        """
        return self.total_input_tokens, self.total_output_tokens
