from heshly_core.models.memory import (
    CustomerMemory,
)


class MemoryPromptBuilder:
    """
    Builds the customer memory portion of the AI prompt.
    """

    def build(
        self,
        memory: CustomerMemory,
    ) -> str:

        lines = [
            "Customer Memory:",
            "",
        ]

        if not memory.memories:

            lines.append(
                "No customer memory available."
            )

            return "\n".join(lines)

        for item in memory.memories:

            key = item.key.replace(
                "_",
                " "
            ).title()

            lines.append(
                f"- {key}: {item.value}"
            )

        return "\n".join(lines)