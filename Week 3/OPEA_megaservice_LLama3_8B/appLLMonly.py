import os
import time
from comps import MicroService, ServiceOrchestrator, ServiceType, ServiceRoleType
# IMPORTANT: Removed 'Usage' from this import because we define it locally below.
from comps.cores.proto.api_protocol import ChatCompletionRequest, ChatCompletionResponse, ChatCompletionResponseChoice, ChatMessage
from pydantic import BaseModel # Needed to define our local Usage class
from typing import Dict # Import Dict for type hinting in schedule method

# --- Environment Variables ---
EMBEDDING_SERVICE_HOST_IP = os.getenv("EMBEDDING_SERVICE_HOST_IP", "0.0.0.0")
EMBEDDING_SERVICE_PORT = os.getenv("EMBEDDING_SERVICE_PORT", 6000)

LLM_SERVICE_HOST_IP = os.getenv("LLM_SERVICE_HOST_IP", "0.0.0.0")
LLM_SERVICE_PORT = os.getenv("LLM_SERVICE_PORT", 9000)

MEGA_SERVICE_HOST_IP = os.getenv("MEGA_SERVICE_HOST_IP", "0.0.0.0")
MEGA_SERVICE_PORT = os.getenv("MEGA_SERVICE_PORT", 7000)

# --- Define Usage class locally since it's not importable from comps ---
# This class mimics the structure required by the OpenAI-compatible response.
class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ExampleService:
    def __init__(self, host="0.0.0.0", port=8000):
        print('ello')
        self.host = host
        self.port = port
        self.megaservice = ServiceOrchestrator()
        self.endpoint = "/v1/chat/completions"

    def add_remote_service(self):
        print(f"Configuring LLM Service: {LLM_SERVICE_HOST_IP}:{LLM_SERVICE_PORT}")
        llm = MicroService(
            name="llm", # Name of the LLM service as defined in the orchestrator
            host=LLM_SERVICE_HOST_IP,
            port=LLM_SERVICE_PORT,
            endpoint="/v1/chat/completions",
            use_remote_service=True,
            service_type=ServiceType.LLM,
        )
        self.megaservice.add(llm)
        self.megaservice.flow_to(llm, llm) # Flow from llm to llm for a single-service chain
        print("Megaservice flow configured: LLM only")


    async def handle_request(self, request: ChatCompletionRequest):
        print(f"Megaservice received request in handle_request: {request.messages}")

        input_text = ""
        for message in request.messages:
            if message.get("role") == "user":
                input_text = message.get("content", "")

        # Prepare the input for the orchestrator's 'schedule' method
        # It expects 'initial_inputs' which will be passed to the first service in the flow.
        flow_input = {"messages": request.messages}

        try:
            # Call 'schedule' instead of 'run_flow'.
            # It returns a tuple: (result_dict, runtime_graph)
            # We are interested in the first element, the result_dict.
            flow_result_dict, _ = await self.megaservice.schedule(initial_inputs=flow_input)

            print(f"Megaservice flow executed. Raw result from LLM service: {flow_result_dict}")

            llm_response_content = "Failed to get content from LLM."
            # The 'schedule' method returns a dictionary where keys are service names
            # and values are their responses. Our LLM service is named 'llm'.
            if flow_result_dict and isinstance(flow_result_dict, dict):
                llm_service_response = flow_result_dict.get('llm') # Get response specifically from 'llm' service
                if llm_service_response and isinstance(llm_service_response, dict):
                    if 'choices' in llm_service_response and len(llm_service_response['choices']) > 0:
                        first_choice = llm_service_response['choices'][0]
                        if 'message' in first_choice and 'content' in first_choice['message']:
                            llm_response_content = first_choice['message']['content']
                    elif 'response' in llm_service_response and isinstance(llm_service_response['response'], str):
                        llm_response_content = llm_service_response['response']
                    elif 'text' in llm_service_response and isinstance(llm_service_response['text'], str):
                        llm_response_content = llm_service_response['text']
                # Fallback for unexpected direct response format if 'llm' key is not structured as expected
                elif 'choices' in flow_result_dict and len(flow_result_dict['choices']) > 0:
                     first_choice = flow_result_dict['choices'][0]
                     if 'message' in first_choice and 'content' in first_choice['message']:
                         llm_response_content = first_choice['message']['content']
                elif 'response' in flow_result_dict and isinstance(flow_result_dict['response'], str):
                     llm_response_content = flow_result_dict['response']
                elif 'text' in flow_result_dict and isinstance(flow_result_dict['text'], str):
                     llm_response_content = flow_result_dict['text']


            choice = ChatCompletionResponseChoice(
                index=0,
                message=ChatMessage(role="assistant", content=llm_response_content),
                finish_reason="stop" # Standard finish reason for a complete response
            )

            # Create a Usage object using our locally defined class
            response_usage = Usage(
                prompt_tokens=len(input_text.split()),  # Simple token count based on words
                completion_tokens=len(llm_response_content.split()),
                total_tokens=len(input_text.split()) + len(llm_response_content.split())
            )

            return ChatCompletionResponse(
                id="chatcmpl-" + str(int(time.time())),
                choices=[choice],
                created=int(time.time()),
                model=request.model if request.model else "default-llm-model",
                object="chat.completion",
                # Convert our local Usage object to a dictionary using .model_dump()
                usage=response_usage.model_dump()
            )

        except Exception as e:
            print(f"Error during megaservice flow execution: {e}")
            error_choice = ChatCompletionResponseChoice(
                index=0,
                message=ChatMessage(role="assistant", content=f"Error in megaservice processing: {e}. Please ensure your LLM microservice is running."),
                finish_reason="stop"
            )
            # Create a Usage object for the error response
            error_usage = Usage(
                prompt_tokens=len(input_text.split()),
                completion_tokens=0, # No completion if there's an error
                total_tokens=len(input_text.split())
            )
            return ChatCompletionResponse(
                id="error-" + str(int(time.time())),
                choices=[error_choice],
                created=int(time.time()),
                model=request.model if request.model else "default-llm-model",
                object="chat.completion",
                # Convert our local Usage object to a dictionary using .model_dump()
                usage=error_usage.model_dump()
            )


    def start(self):
        self.service = MicroService(
            self.__class__.__name__,
            service_role=ServiceRoleType.MEGASERVICE,
            host=self.host,
            port=self.port,
            endpoint=self.endpoint,
            input_datatype=ChatCompletionRequest,
            output_datatype=ChatCompletionResponse,
        )

        self.service.add_route(self.endpoint, self.handle_request, methods=["POST"])

        print(f"Starting OPEA Megaservice as a MicroService on {self.host}:{self.port}")
        self.service.start()


if __name__ == "__main__":
    example = ExampleService(host=MEGA_SERVICE_HOST_IP, port=MEGA_SERVICE_PORT)
    example.add_remote_service()
    example.start()