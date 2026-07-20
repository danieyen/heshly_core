from heshly_core.models.personality import (
    BrandVoice,
)


class BrandVoiceEngine:
    """
    Generates prompt instructions that make
    AI responses follow a business's brand voice.
    """

    def build_instruction(
        self,
        brand_voice: BrandVoice,
    ) -> str:

        instructions = [

            (
                f"You are representing "
                f"{brand_voice.business_name}."
            ),

            (
                f"Industry: "
                f"{brand_voice.industry}."
            ),
        ]


        if brand_voice.preferred_terms:

            instructions.append(

                "Prefer these business terms: "

                + ", ".join(
                    brand_voice.preferred_terms
                )

                + "."
            )


        if brand_voice.forbidden_terms:

            instructions.append(

                "Avoid these terms: "

                + ", ".join(
                    brand_voice.forbidden_terms
                )

                + "."
            )


        if brand_voice.allow_emojis:

            instructions.append(
                "Emojis may be used sparingly."
            )

        else:

            instructions.append(
                "Do not use emojis."
            )


        if brand_voice.use_markdown:

            instructions.append(
                "Markdown formatting is allowed."
            )

        else:

            instructions.append(
                "Use plain text formatting."
            )


        return "\n".join(
            instructions
        )