from flask import Flask
from NOCTitlebyER import create_dash_app as create_dash_app1
from ERbyNOCTitle import create_dash_app as create_dash_app2

# Initialize the Flask app
server = Flask(__name__)

# Create and integrate the Dash apps into the Flask server
app1 = create_dash_app1(server)
app2 = create_dash_app2(server)

# Running the Flask app
if __name__ == '__main__':
    server.run(debug=True)