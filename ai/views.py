import os
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from dotenv import load_dotenv

load_dotenv()

HF_API_KEY = os.getenv("HF_API_KEY")

class HuggingFaceChatView(APIView):
    def post(self, request):
        user_message = request.data.get("message")
        if not user_message:
            return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            "Authorization": f"Bearer {HF_API_KEY}",
            "Content-Type": "application/json",
        }

        data = {"inputs": user_message}
        API_URL = "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct"

        try:
            response = requests.post(API_URL, headers=headers, json=data)
            result = response.json()

            # Debug log
            print("HuggingFace response:", result)

            if response.status_code == 200:
                if isinstance(result, list) and "generated_text" in result[0]:
                    ai_reply = result[0]["generated_text"]
                    return Response({"reply": ai_reply}, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Unexpected response", "details": result}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({"error": "Hugging Face API error", "details": result}, status=response.status_code)
        except Exception as e:
            print("Error:", e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
