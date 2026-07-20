"""
Mock Payment Provider
"""


class MockPaymentService:


    def __init__(self):

        self.transactions = []



    def charge(
        self,
        customer_id,
        amount,
    ):

        payment = {

            "payment_id":
                f"pay_{len(self.transactions)+1}",

            "customer_id":
                customer_id,

            "amount":
                amount,

            "status":
                "success",

        }

        self.transactions.append(
            payment
        )

        return payment



    def refund(
        self,
        payment_id,
    ):

        return {

            "payment_id":
                payment_id,

            "status":
                "refunded",

        }



    def health(self):

        return {

            "service": "payment",

            "status": "healthy",

        }
