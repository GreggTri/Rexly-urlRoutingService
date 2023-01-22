from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pymongo import MongoClient
import os
from amplitude import *
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

try:
    app.mongodb_client = MongoClient(host=os.getenv('MONGO_URL'))
    app.db = app.mongodb_client[os.getenv('DB_NAME')]
    app.amplitude = Amplitude(os.getenv('AMP_API_KEY'))
    print("connected to database!")
except Exception as e:
    print("Error: ", e)
    
origins = [
    os.getenv('REXLY_BACKEND')
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
def healthCheck(req: Request, res: Response):
    res.status_code = status.HTTP_200_OK
    return 'ok'

@app.post('/{short_url}')
def redirection(req: Request, res: Response, short_url):
    if len(short_url) != 5:
        res.status_code = status.HTTP_400_BAD_REQUEST
        return f'<h1>This is not a correct url</h1>'
    
    url = req.app.db['urls'].find_one({"short":short_url})
    if url:
        req.app.amplitude.track(BaseEvent(
                event_type='Product Link Clicked',
                user_id=str(url.user_id),
            ))
        req.app.amplitude.shutdown()
        
        return RedirectResponse(url.long, status.HTTP_303_SEE_OTHER)
    else:
        res.status_code = status.HTTP_404_NOT_FOUND
        return f'<h1>404 ERROR: URL NOT FOUND</h1>'