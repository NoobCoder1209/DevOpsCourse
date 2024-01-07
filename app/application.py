# Import the Flask module for your application and define your app.
from flask import Flask, render_template
app = Flask(__name__)
# Define the basic route and the request handler.
@app.route('/')
def home():
	return render_template('index.html')
# Run the application.
if __name__ == '__main__':
	app.run(debug=True,host='0.0.0.0')
