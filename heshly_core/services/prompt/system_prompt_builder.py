class SystemPromptBuilder:
    """
    Builds the permanent system prompt for the AI.
    Contract must be deterministic for n8n AI receptionist node.
    """

    def build(
        self,
        business_name: str,
        business_type: str,
    ) -> str:

        if not business_name or not business_name.strip():
            raise ValueError("business_name is required")
        if not business_type or not business_type.strip():
            raise ValueError("business_type is required")

        business_name = business_name.strip()
        business_type = business_type.strip()

        lines = [

            f"You are the AI receptionist for {business_name}.",

            f"The business is a {business_type}.",

            "",

            "Your responsibilities:",

            "- Welcome customers politely.",

            "- Answer questions accurately.",

            "- Collect missing information one question at a time.",

            "- Help customers book appointments.",

            "- Escalate to a human when necessary.",

            "",

            "Rules:",

            "- Never invent business information.",

            "- Never promise unavailable appointments.",

            "- Be concise and professional.",

            "- If information is missing, ask for it instead of guessing.",

            "- Maintain a friendly conversational tone.",

            "- Always return a valid Action (ask_service, ask_date, ask_time, present_options, create_appointment, escalate_human, answer_question).",

            "- When booking, ensure service, date, and time are collected before calling availability.",

        ]

        return "\n".join(lines)

    def build_with_context(
        self,
        business_name: str,
        business_type: str,
        tenant_id: str | None = None,
        language: str = "en",
    ) -> str:
        base = self.build(business_name, business_type)
        if tenant_id:
            base += f"\n\nTenant: {tenant_id}"
        if language and language != "en":
            base += f"\nRespond in {language}."
        return base
