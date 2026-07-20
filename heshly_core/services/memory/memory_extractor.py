from heshly_core.models.memory import (
    MemoryItem,
    MemoryType,
)


class MemoryExtractor:
    """
    Extracts useful memories from conversation text.
    """


    def extract(
        self,
        message: str,
    ) -> list[MemoryItem]:

        memories = []

        text = message.lower()



        # -----------------------------
        # Identity extraction
        # -----------------------------

        if "my name is" in text:

            name_start = text.find(
                "my name is"
            ) + len("my name is")


            name = (
                message[name_start:]
                .strip()
                .split(".")[0]
                .strip()
            )


            if name:

                memories.append(
                    MemoryItem(
                        key="name",
                        value=name,
                        memory_type=MemoryType.IDENTITY,
                        confidence=0.95,
                    )
                )



        # -----------------------------
        # Preference extraction
        # -----------------------------

        if "prefer" in text:

            pref_start = text.find(
                "prefer"
            ) + len("prefer")


            preference = (
                message[pref_start:]
                .strip()
                .split(".")[0]
                .strip()
            )


            if preference:

                memories.append(
                    MemoryItem(
                        key="preference",
                        value=preference,
                        memory_type=MemoryType.PREFERENCE,
                        confidence=0.85,
                    )
                )



        # -----------------------------
        # Behaviour extraction
        # -----------------------------

        if "usually" in text:

            behavior_start = text.find(
                "usually"
            ) + len("usually")


            behavior = (
                message[behavior_start:]
                .strip()
                .split(".")[0]
                .strip()
            )


            if behavior:

                memories.append(
                    MemoryItem(
                        key="habit",
                        value=behavior,
                        memory_type=MemoryType.BEHAVIOR,
                        confidence=0.80,
                    )
                )


        return memories