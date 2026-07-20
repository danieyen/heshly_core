from heshly_core.models.memory import (
    CustomerMemory,
    MemoryType,
)

from heshly_core.models.customer_profile import (
    CustomerProfile,
)



class CustomerProfileBuilder:
    """
    Converts raw memories into structured profiles.
    """



    def build(
        self,
        memory: CustomerMemory,
    ) -> CustomerProfile:


        profile = CustomerProfile(
            customer_id=memory.customer_id
        )


        for item in memory.memories:


            if item.memory_type == MemoryType.IDENTITY:

                profile.identity[
                    item.key
                ] = item.value



            elif item.memory_type == MemoryType.PREFERENCE:

                profile.preferences.append(
                    item.value
                )



            elif item.memory_type == MemoryType.BEHAVIOR:

                profile.behavior.append(
                    item.value
                )



            elif item.memory_type == MemoryType.HISTORY:

                profile.history.append(
                    item.value
                )



            elif item.memory_type == MemoryType.TEMPORARY:

                profile.temporary.append(
                    item.value
                )


        return profile