-    # 3) No identifier provided - return invalid request with clear message (but success=False)
-    return {
-        "success": False,
-        "message": "conversation_id or phone_number is required",
-        "phone_number": phone_number,
-        "tenant_id": tenant_id,
-        "phone_number_id": phone_number_id,
-    }
+    # 3) No identifier provided - new WhatsApp contact, return empty history with success=True
+    # Allows workflow to continue when conversation_id is empty and phone_number not yet mapped
+    return {
+        "success": True,
+        "conversation": None,
+        "messages": [],
+        "history": [],
+        "phone_number": phone_number,
+        "tenant_id": tenant_id,
+        "phone_number_id": phone_number_id,
+        "message": "No conversation history",
+    }
