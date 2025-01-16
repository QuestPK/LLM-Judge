from waitress import serve
from run import app

if __name__ == "__main__":
    serve(app, host='127.0.0.1', port=5000, threads=2)