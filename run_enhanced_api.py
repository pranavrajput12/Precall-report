import uvicorn

if __name__ == "__main__":
    uvicorn.run("enhanced_api:enhanced_app", host="0.0.0.0", port=8100, reload=True)