# OPEA Megaservice with Llama-3-8B-Instruct

This project sets up an OPEA Megaservice to serve the `meta-llama/Llama-3-8B-Instruct` model using Hugging Face's TGI backend. This version is configured to run on an L4 GPU via LightningAI. Results were greatly improved from the LLama-3-1B-Instruct version I had completed in week 2. 

## Project Overview

The project consists of three main components:

1.  **TGI Server (`tgi.py`):** Runs the TGI server with the Llama-3 8B Instruct model.
2.  **LLM Microservice (`llm_microservice_app.py`):** Acts as a client to the TGI server.
3.  **OPEA Megaservice (`appLLMonly.py`):** The main orchestrator service.

## Instructions to Run

You will need three separate terminals.



# https://github.com/opea-project/GenAIComps
MegaService
A Megaservice is a higher-level architectural construct composed of one or more Microservices, providing the capability to assemble end-to-end applications. Unlike individual Microservices, which focus on specific tasks or functions, a Megaservice orchestrates multiple Microservices to deliver a comprehensive solution.

Megaservices encapsulate complex business logic and workflow orchestration, coordinating the interactions between various Microservices to fulfill specific application requirements. This approach enables the creation of modular yet integrated applications, where each Microservice contributes to the overall functionality of the Megaservice.

Here is a simple example of building Megaservice:

from comps import MicroService, ServiceOrchestrator

EMBEDDING_SERVICE_HOST_IP = os.getenv("EMBEDDING_SERVICE_HOST_IP", "0.0.0.0")
EMBEDDING_SERVICE_PORT = os.getenv("EMBEDDING_SERVICE_PORT", 6000)
LLM_SERVICE_HOST_IP = os.getenv("LLM_SERVICE_HOST_IP", "0.0.0.0")
LLM_SERVICE_PORT = os.getenv("LLM_SERVICE_PORT", 9000)


class ExampleService:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self.megaservice = ServiceOrchestrator()

    def add_remote_service(self):
        embedding = MicroService(
            name="embedding",
            host=EMBEDDING_SERVICE_HOST_IP,
            port=EMBEDDING_SERVICE_PORT,
            endpoint="/v1/embeddings",
            use_remote_service=True,
            service_type=ServiceType.EMBEDDING,
        )
        llm = MicroService(
            name="llm",
            host=LLM_SERVICE_HOST_IP,
            port=LLM_SERVICE_PORT,
            endpoint="/v1/chat/completions",
            use_remote_service=True,
            service_type=ServiceType.LLM,
        )
        self.megaservice.add(embedding).add(llm)
        self.megaservice.flow_to(embedding, llm)
self.gateway = ChatQnAGateway(megaservice=self.megaservice, host="0.0.0.0", port=self.port)


## Check Mega/Micro Service health status and version number

Use the command below to check Mega/Micro Service status.

```bash
curl http://${your_ip}:${service_port}/v1/health_check\
  -X GET \
  -H 'Content-Type: application/json'
Users should get output like below example if Mega/Micro Service works correctly.

{"Service Title":"ChatQnAGateway/MicroService","Version":"1.0","Service Description":"OPEA Microservice Infrastructure"}
